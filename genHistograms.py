import ROOT
# import argparse
import sys
from dataclasses import dataclass

@dataclass
class Entry:
    name: str
    bins: int
    xmin: float
    xmax: float


def main():
    if len(sys.argv) != 4:
        print("usage: python genHistograms.py <input_path> <output_path> <save_all=True>")
    
    input = sys.argv[1]
    output = sys.argv[2]
    wp = sys.argv[3]
    # print(wp)
    print("Generating histograms from:", input, "->", output)
    print(f"WP = {wp}")
    if wp == '0':
        print("Saving all histograms")
        save_all = True
    else:
        print("Saving only efficiency histograms")
        save_all = False

    hist_weight = ROOT.TH1D("hist_weight", "hist_weight", 300, 0, 30)

    if save_all:
        histogram_params = [
            Entry("eps_pass", 100, 0, 50),
            Entry("eps_total", 100, 0, 50),
            Entry("eps_qEta_pass", 24, -2.4, 2.4),
            Entry("eps_qEta_total", 24, -2.4, 2.4),

            Entry("tag_pt", 100, 0, 40),
            Entry("tag_phi", 100, -3.5, 3.5),
            Entry("tag_eta", 100, -3, 3),

            Entry("probe_pt", 100, 0, 40),
            Entry("probe_phi", 100, -3.5, 3.5),
            Entry("probe_eta", 100, -3, 3),
            Entry("probe_aco_presel", 100, 0, 0.2),
            Entry("probe_aco_postsel", 100, 0, 0.2),
            Entry("probe_d0_presel", 400, -200, 200),
            Entry("probe_d0_postsel", 400, -200, 200),
            Entry("probe_dR_presel", 100, 0, 0.3),
            Entry("probe_dR_postsel", 100, 0, 0.03),


            Entry("TPpair_pt_presel", 100, 0, 10),
            Entry("TPpair_pt_postsel", 100, 0, 10),
            Entry("TPpair_dR_presel", 100, 0, 5),
            Entry("TPpair_dR_postsel", 100, 0, 5),
            Entry("TPpair_M_presel", 100, 0, 100),
            Entry("TPpair_M_postsel", 100, 0, 100)
        ]
        hist_eps_cutflow = ROOT.TH1I("hist_eps_cutflow", "hist_eps_cutflow", 20, 0, 20)

        cuts = ["All", "HLT", "nMuon>=1", "track_n<=2", "[ tag loop ]", "muon_is_Loose", "|muon_eta|<2.4", "muon_pt>3", "[ probe loop ]"]
        if "ID_MS" in input:
            cuts = cuts + ["opposite charge", "|track_d0|<2", "tp pair pt<2", "tp pair aco<0.02", "[ ms muon loop]", "dR<0.1", "ms muon d0<2"]
        else:
            cuts = cuts + ["opposite charge", "|track_d0|<2", "track_is_LoosePrimary", "tp pair pt<2", "tp pair aco<0.02", "[ muon low pt loop ]", "dR<0.01"]
        for i in range(len(cuts)):
            hist_eps_cutflow.GetXaxis().SetBinLabel(i+1, cuts[i])
    else:
        histogram_params = [
            Entry("eps_pass", 100, 0, 50),
            Entry("eps_total", 100, 0, 50),
            Entry("eps_qEta_pass", 24, -2.4, 2.4),
            Entry("eps_qEta_total", 24, -2.4, 2.4),
        ]
    dR_v_probe_pt = ROOT.TH2D("dR_v_probe_pt", "dR vs. probe pt", 50, 0, 10, 100, 0, 0.3)
    aco_v_probe_pt = ROOT.TH2D("aco_v_probe_pt", "aco vs. probe pt", 50, 0, 10, 100, 0, 0.3)
    # histograms = []
    # for entry in histogram_params:
        # histograms.append(ROOT.TH1D("hist_"+entry.name, "hist_"+entry.name, entry.bins, entry.xmin, entry.xmax))
    histograms = {e.name: ROOT.TH1D(e.name, e.name, e.bins, e.xmin, e.xmax) for e in histogram_params}


    f_in = ROOT.TFile(input)
    tree = f_in.Get("G2TauTree_output")
    # print("Generating histograms from:", input, "->", output)



    j = 0
    total_events = tree.GetEntries()
    for event in tree:
        if j % 10000 == 0:
            print(f"\rProgress: {j} / {total_events}", end="", flush=True)
        j += 1
        weight = getattr(event, "weight")
        hist_weight.Fill(weight)

        if save_all:
            vals = getattr(event, "eps_cutflow")
            for val in vals:
                hist_eps_cutflow.Fill(val)
            for entry in histogram_params:
                vals = getattr(event, entry.name)
                for val in vals:
                    histograms[entry.name].Fill(val, weight)
            
            vals_pt = getattr(event, "eps_total")
            vals_dR = getattr(event, "probe_dR_presel")

            vals_pair_pt = getattr(event, "TPpair_pt_presel")
            vals_aco = getattr(event, "probe_aco_presel")

            for val_pt in vals_pt:
                for val_dR in vals_dR:
                    dR_v_probe_pt.Fill(val_pt, val_dR, weight)
            for val_pair_pt in vals_pair_pt:
                for val_aco in vals_aco:
                    aco_v_probe_pt.Fill(val_pair_pt, val_aco, weight)
        
    print(f"\rProgress: {total_events} / {total_events}", end="", flush=True)
    print("\n[ Done ]")
    print("")
    
    f_out = ROOT.TFile(output, "RECREATE")
    hist_weight.Write()
    for h in histograms.values():
        h.Write()
    if save_all:
        hist_eps_cutflow.Write()
        dR_v_probe_pt.Write()
        aco_v_probe_pt.Write()
    
    f_out.Close()

    f_in.Close()

if __name__ == "__main__":
    main()