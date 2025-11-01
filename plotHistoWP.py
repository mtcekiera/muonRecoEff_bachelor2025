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
    "Tight WP, aco<0.01",
    "Tight WP, aco<0.03",
    "ZDC cuts"
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

def _draw_category_page(canvas, out_pdf, hname, use_logy, items, colors, title_prefix, legend_prefix):
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
        lbl = labels[wp_idx] if wp_idx < len(labels) else f"w{wp_idx}"
        leg.AddEntry(h, f"{legend_prefix} {lbl}", "lep")
    leg.Draw()

    canvas.Print(out_pdf)

def main():
    if len(sys.argv) != 2:
        print("Usage: python plot_wp_split.py <ID_MS|mu_ID>")
        sys.exit(1)

    analysis = sys.argv[1]
    base = os.path.join("output", analysis)
    if not os.path.isdir(base):
        print(f"Error: directory '{base}' not found")
        sys.exit(1)

    os.makedirs("histograms", exist_ok=True)
    style()
    c = ROOT.TCanvas("c", "c", 900, 700)
    colors = [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2, ROOT.kMagenta+2]
    wp_dirs = [f"w{i}" for i in range(5)]

    # Open two PDFs
    out_pdf_data = f"histograms/wp_{analysis}_data.pdf"
    out_pdf_mc   = f"histograms/wp_{analysis}_mc.pdf"
    c.Print(out_pdf_data + "[")
    c.Print(out_pdf_mc + "[")

    for hname, use_logy in HIST_CONFIG.items():
        data_items = []  # (wp_index, hist)
        mc_items   = []  # (wp_index, hist)

        for i, wp in enumerate(wp_dirs):
            wpath = os.path.join(base, wp)
            data_path = os.path.join(wpath, "data23_histograms.root")
            mc_path   = os.path.join(wpath, "mc_histograms.root")
            if not (os.path.exists(data_path) and os.path.exists(mc_path)):
                print(f"{wp}: missing ROOT files")
                continue

            fdata = ROOT.TFile.Open(data_path)
            fmc   = ROOT.TFile.Open(mc_path)
            hdata = get_hist(fdata, hname)
            hmc   = get_hist(fmc, hname)
            fdata.Close(); fmc.Close()

            if hdata:
                _style_data(hdata, colors[i])
                data_items.append((i, hdata))
            if hmc:
                _style_mc(hmc, colors[i])
                mc_items.append((i, hmc))

        # Data page for this histogram
        _draw_category_page(c, out_pdf_data, hname, use_logy, data_items, colors, analysis, "Data")
        # MC page for this histogram
        _draw_category_page(c, out_pdf_mc,   hname, use_logy, mc_items,   colors, analysis, "MC")

    # Close PDFs
    c.Print(out_pdf_data + "]")
    c.Print(out_pdf_mc + "]")
    print(f"Wrote: {out_pdf_data}")
    print(f"Wrote: {out_pdf_mc}")

if __name__ == "__main__":
    main()
