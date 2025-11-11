#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import ROOT
ROOT.gROOT.SetBatch(True)

# -------- CONFIG --------
# Map histogram name → logy setting
HIST_CONFIG = {
    "eps_pass":        True,
    "eps_total":        True,
    "eps_qEta_pass":    False,
    "eps_qEta_total":   False,

    "tag_pt":   True,
    "tag_phi":  False,
    "tag_eta":  False,

    "probe_pt":     True,
    "probe_phi":    False,
    "probe_eta":    False,
    
    "probe_aco_presel":     True,
    "probe_aco_postsel":    True,
    "probe_d0_presel":      True,
    "probe_d0_postsel":     True,
    "probe_dR_presel":      False,
    "probe_dR_postsel":     False,


    "TPpair_pt_presel":     True,
    "TPpair_pt_postsel":    True,
    "TPpair_dR_presel":     True,
    "TPpair_dR_postsel":    True,
    "TPpair_M_presel":      True,
    "TPpair_M_postsel":     True
}



labels = [
    "Initial",
    "Tight WP",
    "aco<0.01",
    "aco<0.03",
    "ZDC cuts"
]

markers_data = [
    20, 21, 22, 23, 29
]
markers_mc = [
    24, 25, 26, 27, 30
]
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
    if not file: return None
    h = file.Get(name)
    if not h:
        for key in file.GetListOfKeys():
            obj = file.Get(key.GetName())
            if isinstance(obj, ROOT.TDirectory):
                sub = obj.Get(name)
                if sub:
                    h = sub
                    break
    if not h: return None
    h = h.Clone(f"{h.GetName()}__clone")
    h.SetDirectory(0)
    return h

def _style_data(h, color):
    h.SetLineColor(color)
    h.SetMarkerColor(color)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(0.9)
    h.SetLineWidth(2)

def _style_mc(h, color):
    h.SetLineColor(color)
    h.SetLineStyle(2)
    h.SetLineWidth(2)

def _draw_category_page(canvas, out_pdf, hname, use_logy, items, colors, title_prefix, legend_prefix, is_data):
    """
    items: list of (wp_index, TH1) for one category (data OR mc)
    """
    if not items: return
    canvas.cd(); canvas.Clear()
    canvas.SetLogy(use_logy)
    canvas.SetGridx(True); canvas.SetGridy(True)

    h0 = items[0][1]
    # Y range
    ymax = max(h.GetMaximum() for _, h in items)
    if use_logy:
        for _, h in items: h.SetMinimum(1e-3)
        h0.SetMaximum(ymax * 10.0)
    else:
        h0.SetMinimum(0.0)
        h0.SetMaximum(ymax * 1.35)

    # Title and draw
    h0.SetTitle(f"{title_prefix} | {hname}")
    h0.Draw("E1")  # for data; OK for mc too
    for _, h in items[1:]:
        h.Draw("E1 SAME")  # use markers/lines already set

    # Legend mapped by working-point index -> label
    leg = ROOT.TLegend(0.60, 0.70, 0.88, 0.88)
    leg.SetBorderSize(0); leg.SetFillStyle(0)
    for wp_idx, h in items:
        h.SetMarkerStyle(markers_data[wp_idx] if is_data else markers_mc[wp_idx])
        h.SetMarkerSize(2)
        h.SetMarkerColor(colors[wp_idx])
        lbl = labels[wp_idx] if wp_idx < len(labels) else f"w{wp_idx}"
        leg.AddEntry(h, f"{legend_prefix} {lbl}", "lep")
    leg.Draw()

    canvas.Print(out_pdf)

def main():
    if len(sys.argv) not in (4,5):
        print("Usage: python3 plotHistoWP.py <ID_MS|mu_ID> <input file> <output file> [Data|MC]")
        sys.exit(1)

    analysis = sys.argv[1]
    input_fname = sys.argv[2]
    out_pdf = sys.argv[3]
    is_data = True
    if(len(sys.argv)==5):
        if(sys.argv[4].lower() == "mc"):
            is_data = False

    base = os.path.join("output", analysis)
    if not os.path.isdir(base):
        print(f"Error: directory '{base}' not found")
        sys.exit(1)

    style()
    c = ROOT.TCanvas("c", "c", 900, 700)
    colors = [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2, ROOT.kMagenta+2]
    wp_dirs = [f"w{i}" for i in range(5)]

    # Open two PDFs
    c.Print(out_pdf + "[")

    for hname, use_logy in HIST_CONFIG.items():
        data_items = []  # (wp_index, hist)

        for i, wp in enumerate(wp_dirs):
            wpath = os.path.join(base, wp)
            data_path = os.path.join(wpath, input_fname)
            if not (os.path.exists(data_path)):
                print(f"{wp}: missing ROOT files")
                continue

            fdata = ROOT.TFile.Open(data_path)
            hdata = get_hist(fdata, hname)
            fdata.Close()

            if hdata:
                _style_data(hdata, colors[i])
                data_items.append((i, hdata))

        _draw_category_page(c,      out_pdf, hname, use_logy, data_items,   colors, analysis, "", True)
# def     _draw_category_page(canvas, out_pdf, hname, use_logy, items,        colors, title_prefix, legend_prefix, is_data):

    c.Print(out_pdf + "]")
    print(f"Wrote: {out_pdf}")

if __name__ == "__main__":
    main()
