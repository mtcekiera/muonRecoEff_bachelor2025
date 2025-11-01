#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import ROOT
ROOT.gROOT.SetBatch(True)

# -------- CONFIG --------
# Map histogram name → logy setting
HIST_CONFIG = {
    "TPpair_M_postsel": True,
    "tag_pt": True,
    "tag_eta": False
}
# ------------------------

def style():
    s = ROOT.gStyle
    s.SetOptStat(0)
    s.SetTitleFont(42, "XYZ")
    s.SetLabelFont(42, "XYZ")
    s.SetTitleSize(0.05, "XYZ")
    s.SetLabelSize(0.045, "XYZ")
    s.SetPadGridX(True)
    s.SetPadGridY(True)

def get_hist(file, name):
    if not file:
        return None
    h = file.Get(name)
    if not h:
        for key in file.GetListOfKeys():
            obj = file.Get(key.GetName())
            if isinstance(obj, ROOT.TDirectory):
                sub = obj.Get(name)
                if sub:
                    h = sub
                    break
    if not h:
        return None
    h = h.Clone(f"{h.GetName()}__clone")
    h.SetDirectory(0)
    return h

def main():
    if len(sys.argv) != 2:
        print("Usage: python plot_wp_all.py <ID_MS|mu_ID>")
        sys.exit(1)

    base = os.path.join("output", sys.argv[1])
    if not os.path.isdir(base):
        print(f"Error: directory '{base}' not found")
        sys.exit(1)

    style()
    c = ROOT.TCanvas("c", "c", 900, 700)
    out_pdf = f"histograms/wp_{sys.argv[1]}.pdf"
    c.Print(out_pdf + "[")

    wp_dirs = [f"w{i}" for i in range(5)]
    colors = [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2, ROOT.kMagenta+2]

    for hname, use_logy in HIST_CONFIG.items():
        histos_data, histos_mc, labels = [], [], []
        print(f"\nHistogram: {hname} (logy={use_logy})")

        for i, wp in enumerate(wp_dirs):
            wpath = os.path.join(base, wp)
            data_path = os.path.join(wpath, "data23_histograms.root")
            mc_path   = os.path.join(wpath, "mc_histograms.root")

            if not (os.path.exists(data_path) and os.path.exists(mc_path)):
                print(f"  {wp}: missing ROOT files")
                continue

            fdata = ROOT.TFile.Open(data_path)
            fmc   = ROOT.TFile.Open(mc_path)
            hdata = get_hist(fdata, hname)
            hmc   = get_hist(fmc, hname)
            fdata.Close(); fmc.Close()

            if not hdata and not hmc:
                print(f"  {wp}: histogram '{hname}' not found")
                continue

            if hdata:
                hdata.SetLineColor(colors[i])
                hdata.SetMarkerColor(colors[i])
                hdata.SetMarkerStyle(20)
                hdata.SetMarkerSize(0.8)
                hdata.SetLineWidth(2)
                histos_data.append(hdata)
            if hmc:
                hmc.SetLineColor(colors[i])
                hmc.SetLineStyle(2)
                hmc.SetLineWidth(2)
                histos_mc.append(hmc)

            labels.append(f"w{i}")
            # print(f"  found in {wp}")

        if not histos_data and not histos_mc:
            print(f"  No histograms found for '{hname}', skipping page.")
            continue

        c.cd(); c.Clear()
        c.SetLogy(use_logy)
        allh = histos_data + histos_mc
        maxy = max([h.GetMaximum() for h in allh]) if allh else 1

        if use_logy:
            for h in allh:
                h.SetMinimum(1e-3)
            allh[0].SetMaximum(maxy * 10)
        else:
            allh[0].SetMaximum(maxy * 1.3)

        allh[0].SetTitle(f"{sys.argv[1]} | {hname}")
        allh[0].Draw("E1" if "data" in allh[0].GetName() else "HIST")
        for h in allh[1:]:
            opt = "E1 SAME" if "data" in h.GetName() else "HIST SAME"
            h.Draw(opt)

        leg = ROOT.TLegend(0.60, 0.70, 0.88, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        for i, lbl in enumerate(labels):
            if i < len(histos_data):
                leg.AddEntry(histos_data[i], f"data23 {lbl}", "lep")
            if i < len(histos_mc):
                leg.AddEntry(histos_mc[i], f"mc {lbl}", "l")
        leg.Draw()

        c.Print(out_pdf)

    c.Print(out_pdf + "]")
    print(f"\nOutput written to: {out_pdf}")

if __name__ == "__main__":
    main()
