#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import ROOT
from array import array

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

# ---------- CONFIG ----------
BIN_EDGES = [1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.5, 7.5, 10.0, 12.5, 15.0, 50.0]
HNAME_PASS  = "eps_pass"
HNAME_TOTAL = "eps_total"

# Styling
MARKER_SIZE     = 2
LINE_WIDTH_DATA = 2
LINE_WIDTH_MC   = 3
# ---------------------------------------------------------
labels = [
    "Initial",
    "Tight WP",    
    "Tight WP, aco<0.01",    
    "Tight WP, aco<0.03",
    "ZDC cuts",
    "no d0 cut"
]
markers_data = [
    20, 21, 22, 23, 29, 30
]
markers_mc = [
    24, 25, 26, 27, 30, 31
]
def style():
    s = ROOT.gStyle
    s.SetOptStat(0)
    s.SetTitleFont(42, "XYZ")
    s.SetLabelFont(42, "XYZ")
    s.SetTitleSize(0.05, "XYZ")
    s.SetLabelSize(0.045, "XYZ")
    s.SetPadGridX(True)
    s.SetPadGridY(True)

def _find_hist_recursive(d, name):
    h = d.Get(name)
    if h: return h
    for key in d.GetListOfKeys():
        obj = d.Get(key.GetName())
        if isinstance(obj, ROOT.TDirectory):
            h2 = _find_hist_recursive(obj, name)
            if h2: return h2
    return None

def _rebin_to(h, edges):
    nb = len(edges) - 1
    return h.Rebin(nb, h.GetName() + "__rebin", array('d', edges))

def build_efficiency_single_file(path, hname_pass, hname_total, edges):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie(): return None
    h_pass  = _find_hist_recursive(f, hname_pass)
    h_total = _find_hist_recursive(f, hname_total)
    if not h_pass or not h_total:
        f.Close(); return None
    h_pass  = _rebin_to(h_pass,  edges).Clone(h_pass.GetName()+"__cl");  h_pass.SetDirectory(0)
    h_total = _rebin_to(h_total, edges).Clone(h_total.GetName()+"__cl"); h_total.SetDirectory(0)
    f.Close()
    if not ROOT.TEfficiency.CheckConsistency(h_pass, h_total):
        print(f"Warning: inconsistent pass/total in {path}")
        return None
    te = ROOT.TEfficiency(h_pass, h_total)
    te.SetStatisticOption(ROOT.TEfficiency.kFNormal)  # sane errors for weighted inputs
    return te

def get_efficiencies(analysis, filename):
    base = os.path.join("output", analysis)
    eff_data = {}
    for i in range(6):
        wp = f"w{i}"
        data_path = os.path.join(base, wp, filename)
        if not (os.path.exists(data_path)):
            print(f"Missing files: {analysis}/{wp}")
            continue
        e_d = build_efficiency_single_file(data_path, HNAME_PASS, HNAME_TOTAL, BIN_EDGES)
        if e_d: eff_data[wp] = e_d
    return eff_data

def combine_total_eff(eff1, eff2):
    if eff1 is None or eff2 is None: return None
    n = eff1.GetTotalHistogram().GetNbinsX()
    gr = ROOT.TGraphAsymmErrors(n)
    for i in range(1, n+1):
        e1 = eff1.GetEfficiency(i);  e2 = eff2.GetEfficiency(i)
        u1 = eff1.GetEfficiencyErrorUp(i);  d1 = eff1.GetEfficiencyErrorLow(i)
        u2 = eff2.GetEfficiencyErrorUp(i);  d2 = eff2.GetEfficiencyErrorLow(i)
        val = e1 * e2
        eup = val * ((u1/e1 if e1>0 else 0.)**2 + (u2/e2 if e2>0 else 0.)**2)**0.5
        edn = val * ((d1/e1 if e1>0 else 0.)**2 + (d2/e2 if e2>0 else 0.)**2)**0.5
        x  = eff1.GetTotalHistogram().GetBinCenter(i)
        ex = eff1.GetTotalHistogram().GetBinWidth(i)/2.0
        gr.SetPoint(i-1, x, val)
        gr.SetPointError(i-1, ex, ex, edn, eup)
    return gr

def draw_single_category_page(c, title, edges, eff_dict, colors, frame_name,
                              label_prefix="data", marker_style=markers_data, line_width=2):
    c.Clear(); c.SetLogx(True); c.SetLogy(False); c.SetGridx(True); c.SetGridy(True)

    frame = ROOT.TH1F(frame_name, "", len(edges)-1, array('d', edges))
    frame.SetMinimum(0.0); frame.SetMaximum(1.1)
    frame.SetTitle(title)
    frame.GetXaxis().SetTitle("p_{T} [GeV]")
    frame.GetYaxis().SetTitle("Efficiency")
    frame.Draw()

    leg = ROOT.TLegend(0.60, 0.15, 0.90, 0.50)
    leg.SetBorderSize(0); leg.SetFillStyle(0)

    keep = [frame, leg]
    for i in range(6):
        wp = f"w{i}"
        if wp not in eff_dict: 
            continue
        g = eff_dict[wp].CreateGraph()
        g.SetLineColor(colors[i]); g.SetLineWidth(line_width)  # error-bar thickness
        g.SetMarkerColor(colors[i]); g.SetMarkerStyle(marker_style[i]); g.SetMarkerSize(MARKER_SIZE)
        g.Draw("PZ SAME")  # points + asymmetric errors, no connecting lines
        leg.AddEntry(g, f"{labels[i]}", "p")
        keep.append(g)

    leg.Draw(); c.Update()
    return keep

def write_pdf(filename, eff_idms, eff_muid, colors, is_data=True):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    c = ROOT.TCanvas("c_"+("data" if is_data else "mc"), "c", 900, 700)
    c.Print(filename + "[")

    # 1) ε(ID||MS)
    _k1 = draw_single_category_page(
        c, r"#varepsilon(ID||MS)", BIN_EDGES, eff_idms, colors,
        "frame_idms_" + ("data" if is_data else "mc"),
        label_prefix=("data" if is_data else "mc"),
        marker_style=(markers_data if is_data else markers_mc),
        line_width=(LINE_WIDTH_DATA if is_data else LINE_WIDTH_MC),
    )
    c.Print(filename)

    # 2) ε(μ||ID)
    _k2 = draw_single_category_page(
        c, r"#varepsilon(#mu||ID)", BIN_EDGES, eff_muid, colors,
        "frame_muid_" + ("data" if is_data else "mc"),
        label_prefix=("data" if is_data else "mc"),
        marker_style=(markers_data if is_data else markers_mc),
        line_width=(LINE_WIDTH_DATA if is_data else LINE_WIDTH_MC),
    )
    c.Print(filename)

    # 3) Total ε(μ)
    c.Clear(); c.SetLogx(True); c.SetLogy(False); c.SetGridx(True); c.SetGridy(True)
    frame = ROOT.TH1F("frame_total_" + ("data" if is_data else "mc"),
                      "", len(BIN_EDGES)-1, array('d', BIN_EDGES))
    frame.SetMinimum(0.0); frame.SetMaximum(1.1)
    frame.SetTitle(r"Total efficiency  #varepsilon(#mu) = #varepsilon(ID||MS) #times #varepsilon(#mu||ID)")
    frame.GetXaxis().SetTitle("p_{T} [GeV]"); frame.GetYaxis().SetTitle("Efficiency")
    frame.Draw()

    leg = ROOT.TLegend(0.60, 0.15, 0.90, 0.50)
    leg.SetBorderSize(0); leg.SetFillStyle(0)
    keep = [frame, leg]

    for i in range(6):
        wp = f"w{i}"
        if wp in eff_idms and wp in eff_muid:
            gT = combine_total_eff(eff_idms[wp], eff_muid[wp])
            gT.SetLineColor(colors[i]); gT.SetLineWidth(LINE_WIDTH_DATA if is_data else LINE_WIDTH_MC)
            gT.SetMarkerColor(colors[i]); gT.SetMarkerStyle(markers_data[i] if is_data else markers_mc[i]); gT.SetMarkerSize(MARKER_SIZE)
            gT.Draw("PZ SAME"); leg.AddEntry(gT, f"{labels[i]}", "p")
            keep.append(gT)

    leg.Draw(); c.Update()
    c.Print(filename)
    c.Print(filename + "]")

def main():
    if any(e <= 0 for e in BIN_EDGES):
        print("All BIN_EDGES must be > 0 for log-x."); sys.exit(1)
    style()
    colors = [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2, ROOT.kMagenta+2]

    if len(sys.argv) not in (3,4):
        print("Usage: python3 plotHistoWP.py <file name> <output file name> [data|mc]")
    
    filename = sys.argv[1]
    out_filename = sys.argv[2]

    is_data = True
    if len(sys.argv) == 4:
        if sys.argv[3].lower() == "mc":
            is_data = False
    # Build efficiencies once
    eff_IDMS   = get_efficiencies("ID_MS", filename)
    eff_muID   = get_efficiencies("mu_ID", filename)


    # MC-only PDF
    write_pdf(out_filename, eff_IDMS, eff_muID, colors, is_data=is_data)

    print(f"Wrote: {out_filename}")

if __name__ == "__main__":
    main()
