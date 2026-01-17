#!/usr/bin/env python3
import argparse
import sys
import ROOT
import os
import subprocess

VALID_WP = range(0, 8)

def wp_type(s: str) -> int:
    """Custom argparse type for working points 0–6."""
    try:
        v = int(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Working point must be an integer, got '{s}'")

    if v not in VALID_WP:
        raise argparse.ArgumentTypeError(f"Working point must be in {list(VALID_WP)}, got {v}")
    return v


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Driver script for my analysis pipeline"
    )

    parser.add_argument(
        "-a", "--analysis",
        action="store_true",
        help="run the analysis step",
    )
    parser.add_argument(
        "-g", "--generate",
        action="store_true",
        help="run the generation step",
    )
    parser.add_argument("-e", "--efficiency",
        action="store_true",
        help="generate efficiency files",
    )
    parser.add_argument("-s", "--scale-factors",
        action="store_true",
        help="calculate scale factors",
    )
    parser.add_argument("-z",
        action="store_true",
        help="plot scale factors with systematics",
    )


    parser.add_argument(
        "-d", "--dataset",
        choices=["data", "sc", "sl", "mg"],
        nargs="+",
        required=True,
        help="which dataset(s) to process (data/sc/sl/mg)",
    )

    parser.add_argument(
        "-w", "--wp",
        metavar="WP",
        type=wp_type,
        nargs="+",
        required=True,
        help="working points to run (0–6), space-separated",
    )

    args = parser.parse_args(argv)

    if not (args.analysis or args.generate or args.efficiency or args.scale_factors or args.z):
        raise KeyError("No action chosen")

    return args

import os
import subprocess

MC_SAMPLES = {
    "sc": {  # SuperChic
        "name": "SuperChic",
        "tag": "mc_sc",
        "files": [
            ("4m7", 925),
            ("7m20", 265),
            ("20m", 9.74),
        ],
    },
    "sl": {  # StarLight
        "name": "StarLight",
        "tag": "mc_sl",
        "files": [
            ("4m7", 741),
            ("7m20", 207),
            ("20m", 7.14),
        ],
    },
    "mg": {  # MadGraph
        "name": "MadGraph",
        "tag": "mc_mg",
        "files": [
            ("4m7", 921),
            ("7m20", 264),
            ("20m", 9.54),
        ],
    },
}

DATA_INPUT_FILE = "./input/data23.root"


def _run(cmd: list[str], check: bool = False) -> None:
    print(" ".join(cmd))
    proc = subprocess.run(cmd)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, proc.args)
    if not check and proc.returncode != 0:
        print(f"  [warning] command exited with code {proc.returncode}")


def _run_root_macro(input_path: str, output_path: str, mode: int, norm: float, wp: int) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    arg = f'G2TauTree.C("{input_path}", "{output_path}", {mode}, {norm}, {wp})'
    cmd = ["root", "-l", "-q", "-b", arg]
    _run(cmd, check=False)


def _run_hadd(output_path: str, inputs: list[str]) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = ["hadd", "-f", "-v", "0", output_path, *inputs]
    _run(cmd, check=True)


def do_analysis(datasets: list[str], wps: list[int]) -> None:
    """
    Run the analysis step for the selected datasets and working points.

    datasets: list like ["data", "sc", "sl", "mg"]
    wps: list of ints, e.g. [0, 1, 2]
    """
    ordered_mc = ["sc", "sl", "mg"]

    for wp in wps:
        print(f"\n================ WP = {wp} ================\n")

        for ds in ordered_mc:
            if ds not in datasets:
                continue

            cfg = MC_SAMPLES[ds]
            tag = cfg["tag"]
            name = cfg["name"]

            print(f"(MC, {name}) Analysing wp={wp}")

            for suffix, norm in cfg["files"]:
                in_file  = f"./input/{tag}_{suffix}.root"
                out_id   = f"./output/ID_MS/w{wp}/{tag}_{suffix}.root"
                out_mu   = f"./output/mu_ID/w{wp}/{tag}_{suffix}.root"

                _run_root_macro(in_file, out_id, 0, norm, wp)
                _run_root_macro(in_file, out_mu, 1, norm, wp)

            print("Merging files")
            id_out     = f"./output/ID_MS/w{wp}/{tag}.root"
            mu_out     = f"./output/mu_ID/w{wp}/{tag}.root"
            id_inputs  = [f"./output/ID_MS/w{wp}/{tag}_{suf}.root" for suf, _ in cfg["files"]]
            mu_inputs  = [f"./output/mu_ID/w{wp}/{tag}_{suf}.root" for suf, _ in cfg["files"]]

            _run_hadd(id_out, id_inputs)
            _run_hadd(mu_out, mu_inputs)

        if "data" in datasets:
            print(f"(Data) Analysing wp={wp}")

            out_id = f"./output/ID_MS/w{wp}/data23.root"
            out_mu = f"./output/mu_ID/w{wp}/data23.root"

            _run_root_macro(DATA_INPUT_FILE, out_id, 0, 0.0, wp)
            _run_root_macro(DATA_INPUT_FILE, out_mu, 1, 0.0, wp)


def _run_gen_hist(input_path: str, output_path: str, wp: int) -> None:
    """Call: python genHistograms.py in out wp."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        sys.executable,
        "genHistograms.py",
        input_path,
        output_path,
        str(wp),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def do_generation(datasets: list[str], wps: list[int]) -> None:
    """
    Generate histograms for selected datasets and working points.

    datasets: list like ["data", "sc", "sl", "mg"]
    wps: list of ints, e.g. [0, 1, 2]
    """
    print("Generating histograms")

    ordered_mc = ["sc", "sl", "mg"]

    for wp in wps:
        print(f"\n==== Generating histograms for WP = {wp} ====\n")

        for ds in ordered_mc:
            if ds not in datasets:
                continue

            cfg = MC_SAMPLES[ds]
            tag = cfg["tag"]

            in_id  = f"./output/ID_MS/w{wp}/{tag}.root"
            out_id = f"./output/ID_MS/w{wp}/hist_{tag}.root"

            in_mu  = f"./output/mu_ID/w{wp}/{tag}.root"
            out_mu = f"./output/mu_ID/w{wp}/hist_{tag}.root"

            _run_gen_hist(in_id, out_id, wp)
            _run_gen_hist(in_mu, out_mu, wp)

        if "data" in datasets:
            in_id  = f"./output/ID_MS/w{wp}/data23.root"
            out_id = f"./output/ID_MS/w{wp}/hist_data23.root"

            in_mu  = f"./output/mu_ID/w{wp}/data23.root"
            out_mu = f"./output/mu_ID/w{wp}/hist_data23.root"

            _run_gen_hist(in_id, out_id, wp)
            _run_gen_hist(in_mu, out_mu, wp)

def _run_gen_eff(input_path: str, output_path: str, wp:int) -> None:
    """Call: python genEff.py in out."""
    wp_str = str(wp)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        sys.executable,
        "genEff.py",
        input_path,
        output_path,
        wp_str
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def _run_gen_sf(eff_data: str, eff_mc: str, output_path: str, wp:str) -> None:
    """Call: python genSF.py eff_data eff_mc out."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        sys.executable,
        "genSF.py",
        eff_data,
        eff_mc,
        output_path,
        wp
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def _run_plot_sfsyst(sf_file: str, pdf_out: str, obj_name: str) -> None:
    """Call: python plotSFsyst.py sf_file pdf_out obj_name."""
    os.makedirs(os.path.dirname(pdf_out), exist_ok=True)
    cmd = [
        sys.executable,
        "plotSFsyst.py",
        sf_file,
        pdf_out,
        obj_name,
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def do_efficiency(datasets: list[str], wps: list[int]) -> None:
    """
    Generate efficiency files from histogram ROOT files.

    datasets: ["data", "sc", "sl", "mg"] subset
    wps: list of working points, e.g. [0, 1, 2]
    """
    print("Generating efficiency files")

    ordered_mc = ["sc", "sl", "mg"]

    for wp in wps:
        print(f"\n==== Efficiencies for WP = {wp} ====\n")

        if "data" in datasets:
            in_data  = f"w{wp}/hist_data23.root"
            out_data = f"output/eff/w{wp}/eff_data23.root"
            _run_gen_eff(in_data, out_data, wp)

        for ds in ordered_mc:
            if ds not in datasets:
                continue

            tag = MC_SAMPLES[ds]["tag"]
            in_mc  = f"w{wp}/hist_{tag}.root"
            out_mc = f"output/eff/w{wp}/eff_{tag}.root"
            _run_gen_eff(in_mc, out_mc, wp)
def do_scale_factors(datasets: list[str], wps: list[int]) -> None:
    """
    Calculate scale factors from efficiency files.

    datasets: ["data", "sc", "sl", "mg"] subset
    wps: list of working points
    """
    print("Calculating scale factors")

    if "data" not in datasets:
        print("No 'data' dataset selected → cannot compute scale factors.")
        return

    ordered_mc = ["sc", "sl", "mg"]

    for wp in wps:
        print(f"\n==== Scale factors for WP = {wp} ====\n")

        eff_data = f"./output/eff/w{wp}/eff_data23.root"

        for ds in ordered_mc:
            if ds not in datasets:
                continue

            tag = MC_SAMPLES[ds]["tag"]
            eff_mc = f"./output/eff/w{wp}/eff_{tag}.root"
            sf_out = f"./output/eff/w{wp}/sf_{ds}.root"

            _run_gen_sf(eff_data, eff_mc, sf_out, str(wp))

def do_syst_plots(datasets: list[str]) -> None:
    """
    Plot scale factors with systematic errors using plotSFsyst.py.

    Uses the sf_*.root files under output/eff/w0..w6 as in the original bash.
    """
    print("Plotting scale factors with systematic errors")

    # SuperChic
    if "sc" in datasets:
        _run_plot_sfsyst("sf_sc.root", "./histograms/scale_factors/sc_pt.pdf",   "scale_factor_pT")
        _run_plot_sfsyst("sf_sc.root", "./histograms/scale_factors/sc_qeta.pdf", "scale_factor_qEta")

    # StarLight
    if "sl" in datasets:
        _run_plot_sfsyst("sf_sl.root", "./histograms/scale_factors/sl_pt.pdf",   "scale_factor_pT")
        _run_plot_sfsyst("sf_sl.root", "./histograms/scale_factors/sl_qeta.pdf", "scale_factor_qEta")

    # MadGraph
    if "mg" in datasets:
        _run_plot_sfsyst("sf_mg.root", "./histograms/scale_factors/mg_pt.pdf",   "scale_factor_pT")
        _run_plot_sfsyst("sf_mg.root", "./histograms/scale_factors/mg_qeta.pdf", "scale_factor_qEta")



def main(argv=None):
    args = parse_args(argv)

    if args.analysis:
        do_analysis(args.dataset, args.wp)

    if args.generate:
        do_generation(args.dataset, args.wp)

    if args.efficiency:
        do_efficiency(args.dataset, args.wp)

    if args.scale_factors:
        do_scale_factors(args.dataset, args.wp)

    if args.z:
        do_syst_plots(args.dataset)

if __name__ == "__main__":
    main()