#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import ROOT
from array import array

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

# ---------- CONFIG ----------
# Variable-bin edges (strictly > 0 for log-x)
BIN_EDGES = [1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.5, 7.5, 10.0, 12.5, 15.0, 50.0]

# Histogram names inside each file
HNAME_PASS  = "eps_pass"
HNAME_TOTAL = "eps_total"

# Output PDF
OUT_PDF = "histograms/wpEfficiencies.pdf"
# ----------------------------

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
    return ROOT.TEfficiency(h_pass, h_total)

def get_efficiencies(analysis):
    base = os.path.join("output", analysis)
    eff_data, eff_mc = {}, {}
    for i in range(5):
        wp = f"w{i}"
        data_path = os.path.join(base, wp, "data23_histograms.root")
        mc_path   = os.path.join(base, wp, "mc_histograms.root")
        if not (os.path.exists(data_path) and os.path.exists(mc_path)):
            print(f"Missing files: {analysis}/{wp}")
            continue
        e_d = build_efficiency_single_file(data_path, HNAME_PASS, HNAME_TOTAL, BIN_EDGES)
        e_m = build_efficiency_single_file(mc_path,   HNAME_PASS, HNAME_TOTAL, BIN_EDGES)
        if e_d: eff_data[wp] = e_d
        if e_m: eff_mc[wp]   = e_m
    return eff_data, eff_mc

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

def draw_eff_page(c, title, edges, eff_data_dict, eff_mc_dict, colors):
    c.Clear(); c.SetLogx(True); c.SetLogy(False)
    frame = ROOT.TH1F("frame_"+title, "", len(edges)-1, array('d', edges))
    frame.SetMinimum(0.0); frame.SetMaximum(1.1)
    frame.SetTitle(title)
    frame.GetXaxis().SetTitle("p_{T} [GeV]")
    frame.GetYaxis().SetTitle("Efficiency")
    frame.Draw()

    leg = ROOT.TLegend(0.60, 0.15, 0.88, 0.38)
    leg.SetBorderSize(0); leg.SetFillStyle(0)

    keep = []
    for i, wp in enumerate(sorted(eff_data_dict.keys())):
        gdata = eff_data_dict[wp].CreateGraph()
        gdata.SetLineColor(colors[i]); gdata.SetMarkerColor(colors[i])
        gdata.SetMarkerStyle(20); gdata.SetMarkerSize(0.8)
        gdata.Draw("P SAME"); keep.append(gdata)
        leg.AddEntry(gdata, f"data w{wp[-1]}", "p")

        if wp in eff_mc_dict:
            gmc = eff_mc_dict[wp].CreateGraph()
            gmc.SetLineColor(colors[i]); gmc.SetLineStyle(2)
            gmc.Draw("L SAME"); keep.append(gmc)
            leg.AddEntry(gmc, f"mc w{wp[-1]}", "l")

    leg.Draw(); c.Update()
    return keep

def main():
    if any(e <= 0 for e in BIN_EDGES):
        print("All BIN_EDGES must be > 0 for log-x."); sys.exit(1)

    os.makedirs(os.path.dirname(OUT_PDF), exist_ok=True)
    style()
    colors = [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2, ROOT.kMagenta+2]

    c = ROOT.TCanvas("c", "c", 900, 700)
    c.Print(OUT_PDF + "[")

    # 1) ε(ID||MS)
    eff_d_IDMS, eff_m_IDMS = get_efficiencies("ID_MS")
    _k = draw_eff_page(c, r"#varepsilon(ID||MS)", BIN_EDGES, eff_d_IDMS, eff_m_IDMS, colors)
    c.Print(OUT_PDF)

    # 2) ε(μ||ID)
    eff_d_muID, eff_m_muID = get_efficiencies("mu_ID")
    _k = draw_eff_page(c, r"#varepsilon(#mu||ID)", BIN_EDGES, eff_d_muID, eff_m_muID, colors)
    c.Print(OUT_PDF)

    # 3) Total ε(μ) = ε(ID||MS) × ε(μ||ID)
    c.Clear(); c.SetLogx(True); c.SetLogy(False)
    frame = ROOT.TH1F("frame_total", "", len(BIN_EDGES)-1, array('d', BIN_EDGES))
    frame.SetMinimum(0.0); frame.SetMaximum(1.1)
    frame.SetTitle(r"Total efficiency  #varepsilon(#mu) = #varepsilon(ID||MS) #times #varepsilon(#mu||ID)")
    frame.GetXaxis().SetTitle("p_{T} [GeV]")
    frame.GetYaxis().SetTitle("Efficiency")
    frame.Draw()

    leg = ROOT.TLegend(0.60, 0.15, 0.88, 0.38)
    leg.SetBorderSize(0); leg.SetFillStyle(0)
    keep = []

    for i in range(5):
        wp = f"w{i}"
        if wp not in eff_d_IDMS or wp not in eff_d_muID:
            continue
        gD = combine_total_eff(eff_d_IDMS[wp], eff_d_muID[wp])
        gD.SetLineColor(colors[i]); gD.SetMarkerColor(colors[i])
        gD.SetMarkerStyle(20); gD.SetMarkerSize(0.8)
        gD.Draw("P SAME"); keep.append(gD)
        leg.AddEntry(gD, f"data w{i}", "p")

        if wp in eff_m_IDMS and wp in eff_m_muID:
            gM = combine_total_eff(eff_m_IDMS[wp], eff_m_muID[wp])
            gM.SetLineColor(colors[i]); gM.SetLineStyle(2)
            gM.Draw("L SAME"); keep.append(gM)
            leg.AddEntry(gM, f"mc w{i}", "l")

    leg.Draw()
    c.Print(OUT_PDF)

    c.Print(OUT_PDF + "]")
    print(f"Wrote: {OUT_PDF}")

if __name__ == "__main__":
    main()
