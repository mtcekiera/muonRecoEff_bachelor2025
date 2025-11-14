#!/usr/bin/env python3
# usage: python plot_eff_ratio.py data.root mc.root output.pdf
import sys
from array import array
import ROOT as R
R.gROOT.SetBatch(True)

# ---------- ratios ----------
def ratio_of_TEff(e1, e2):
    g = R.TGraphAsymmErrors(); R.SetOwnership(g, False)
    h1, h2 = e1.GetTotalHistogram(), e2.GetTotalHistogram()
    for i in range(1, h1.GetNbinsX() + 1):
        if h1.GetBinContent(i) <= 0 or h2.GetBinContent(i) <= 0:
            continue
        x  = h1.GetXaxis().GetBinCenter(i)
        ex = 0.5 * h1.GetXaxis().GetBinWidth(i)
        a, au, ad = e1.GetEfficiency(i), e1.GetEfficiencyErrorUp(i),  e1.GetEfficiencyErrorLow(i)
        b, bu, bd = e2.GetEfficiency(i), e2.GetEfficiencyErrorUp(i),  e2.GetEfficiencyErrorLow(i)
        if b <= 0: 
            continue
        r = a / b
        r_hi = min(a + au, 1.0) / max(b - bd, 1e-12) - r
        r_lo = r - max(a - ad, 0.0) / min(b + bu, 1.0)
        p = g.GetN()
        g.SetPoint(p, x, r)
        g.SetPointError(p, ex, ex, max(0.0, r_lo), max(0.0, r_hi))
    return g

def ratio_of_TGraphs(g1, g2):
    g = R.TGraphAsymmErrors(); R.SetOwnership(g, False)
    n = min(g1.GetN(), g2.GetN())
    for i in range(n):
        x1 = array('d', [0.0]); y1 = array('d', [0.0])
        x2 = array('d', [0.0]); y2 = array('d', [0.0])
        g1.GetPoint(i, x1, y1); g2.GetPoint(i, x2, y2)
        y2v = y2[0]
        if y2v <= 0: 
            continue
        r = y1[0] / y2v
        eyl1, eyh1 = g1.GetErrorYlow(i),  g1.GetErrorYhigh(i)
        eyl2, eyh2 = g2.GetErrorYlow(i),  g2.GetErrorYhigh(i)
        exl1, exh1 = g1.GetErrorXlow(i),  g1.GetErrorXhigh(i)
        r_hi = (y1[0] + eyh1) / max(y2v - eyl2, 1e-12) - r
        r_lo = r - (y1[0] - eyl1) / min(y2v + eyh2, 1.0)
        p = g.GetN()
        g.SetPoint(p, x1[0], r)
        g.SetPointError(p, exl1, exh1, max(0.0, r_lo), max(0.0, r_hi))
    return g

# ---------- style ----------
def style_obj(o, color, marker):
    # Works for TEfficiency and TGraphAsymmErrors
    o.SetLineColor(color)
    o.SetMarkerColor(color)
    o.SetMarkerStyle(marker)
    o.SetLineWidth(2)

def _log_x_range_from_axis(ax):
    nb = ax.GetNbins(); xmax = ax.GetXmax()
    xmin = None
    for i in range(1, nb + 1):
        lo, hi = ax.GetBinLowEdge(i), ax.GetBinUpEdge(i)
        if hi <= 0: continue
        if lo <= 0: lo = 0.5 * hi
        xmin = lo; break
    if xmin is None or xmin <= 0: xmin = 1e-6
    if xmax <= xmin: xmax = xmin * 10.0
    return xmin, xmax

def _log_x_range_from_graph(gr):
    xmin_pos, xmax = None, None
    for i in range(gr.GetN()):
        x = array('d', [0.0]); y = array('d', [0.0])
        gr.GetPoint(i, x, y)
        xv = x[0]
        if xmax is None or xv > xmax:
            xmax = xv
        if xv > 0 and (xmin_pos is None or xv < xmin_pos):
            xmin_pos = xv
    if xmin_pos is None: xmin_pos = 1e-6
    if xmax is None or xmax <= xmin_pos: xmax = xmin_pos * 10.0
    return xmin_pos, xmax

# ---------- draw ----------
def draw_one(c, data_obj, mc_obj, title):
    c.Clear(); c.Divide(1, 2)
    is_eff = data_obj.InheritsFrom("TEfficiency")

    if is_eff:
        ax = data_obj.GetTotalHistogram().GetXaxis()
        xmin, xmax = _log_x_range_from_axis(ax)
        xtitle = ax.GetTitle() if ax.GetTitle() else "x"
    else:
        xmin, xmax = _log_x_range_from_graph(data_obj)
        xtitle = "x"

    # top pad
    pad1 = c.cd(1)
    pad1.SetPad(0, 0.30, 1, 1)
    pad1.SetBottomMargin(0.02)
    pad1.SetGrid()
    pad1.SetLogx()

    frame_top = pad1.DrawFrame(xmin, 0.0, xmax, 1.05)
    frame_top.SetTitle(f"{title};{xtitle};Efficiency")
    frame_top.GetXaxis().SetLabelSize(0)
    frame_top.GetXaxis().SetTitleSize(0)

    style_obj(data_obj, R.kBlack, 20)
    style_obj(mc_obj,   R.kRed + 1, 24)
    # We have a frame, so "P SAME" works for both TEff and TGraph
    data_obj.Draw("P SAME")
    mc_obj.Draw("P SAME")

    leg = R.TLegend(0.60, 0.18, 0.88, 0.36)
    leg.SetBorderSize(0)
    leg.AddEntry(data_obj, "Data", "pe")
    leg.AddEntry(mc_obj,   "MC",   "pe")
    leg.Draw()

    # bottom pad
    pad2 = c.cd(2)
    pad2.SetPad(0, 0, 1, 0.30)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.35)
    pad2.SetGridy()
    pad2.SetLogx()

    frame_bot = pad2.DrawFrame(xmin, 0.5, xmax, 1.5)
    frame_bot.GetXaxis().SetTitle(xtitle)
    frame_bot.GetYaxis().SetTitle("Data/MC")
    frame_bot.GetYaxis().SetNdivisions(505)
    frame_bot.GetXaxis().SetTitleSize(0.11)
    frame_bot.GetYaxis().SetTitleSize(0.11)
    frame_bot.GetXaxis().SetLabelSize(0.10)
    frame_bot.GetYaxis().SetLabelSize(0.10)
    frame_bot.GetYaxis().SetTitleOffset(0.45)

    one = R.TLine(xmin, 1.0, xmax, 1.0)
    one.SetLineStyle(2); one.Draw()

    gr = ratio_of_TEff(data_obj, mc_obj) if is_eff else ratio_of_TGraphs(data_obj, mc_obj)
    style_obj(gr, R.kBlack, 20)
    gr.Draw("P SAME")

    c.Modified(); c.Update()

# ---------- main ----------
def main():
    if len(sys.argv) != 4:
        print("usage: python plot_eff_ratio.py data.root mc.root output.pdf"); sys.exit(1)
    fD = R.TFile.Open(sys.argv[1])
    fM = R.TFile.Open(sys.argv[2])
    outpdf = sys.argv[3]

    names = ["ID_MS_eff", "mu_ID_eff", "total_eff"]
    pairs = []
    for n in names:
        d, m = fD.Get(n), fM.Get(n)
        if not d or not m:
            print(f"Warning: {n} missing in one of the files"); continue
        pairs.append((d, m, n))
    
    c = R.TCanvas("c", "c", 800, 800)
    c.Print(outpdf + "[")
    for d, m, n in pairs:
        draw_one(c, d, m, n)
        c.Print(outpdf)
    c.Print(outpdf + "]")

if __name__ == "__main__":
    main()
