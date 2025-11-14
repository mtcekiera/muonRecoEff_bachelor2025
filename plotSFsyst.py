#!/usr/bin/env python3
# usage: python plot_syst_bands.py input.root output.pdf
import sys, os, math
from array import array
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetEndErrorSize(0)
ROOT.gStyle.SetHatchesLineWidth(1)
ROOT.gStyle.SetHatchesSpacing(1.2)

BASE_DIR = "output/eff"
FOLDERS  = ["w0", "w1", "w2", "w3", "w4", "w5"]
OBJ_NAME = "scale_factor"
X_MATCH_TOL = 1e-9

def get_graph(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie(): return None
    g = f.Get(OBJ_NAME)
    if not g or not g.InheritsFrom("TGraphAsymmErrors"):
        f.Close(); return None
    g2 = g.Clone()
    if hasattr(g2, "SetDirectory"): g2.SetDirectory(0)
    f.Close()
    return g2

def point(g, i):
    x = array('d', [0.0]); y = array('d', [0.0])
    g.GetPoint(i, x, y)
    return x[0], y[0]

def errs(g, i):
    return (g.GetErrorXlow(i), g.GetErrorXhigh(i),
            g.GetErrorYlow(i), g.GetErrorYhigh(i))

def find_by_x(g, xref, tol=X_MATCH_TOL):
    for j in range(g.GetN()):
        xj, _ = point(g, j)
        if abs(xj - xref) <= tol * max(1.0, abs(xj), abs(xref)):
            return j
    return -1

def build_syst_graph(nom, var, name):
    out = ROOT.TGraphAsymmErrors(); ROOT.SetOwnership(out, False)
    out.SetName(name)
    for i in range(nom.GetN()):
        x0, y0 = point(nom, i)
        exl0, exh0, _, _ = errs(nom, i)
        j = find_by_x(var, x0)
        if j < 0: continue
        _, y1 = point(var, j)
        dy = abs(y0 - y1)
        p = out.GetN()
        out.SetPoint(p, x0, y0)
        out.SetPointError(p, max(exl0, 0.0), max(exh0, 0.0), dy, dy)
    return out

def build_quadrature_band(nom, syst_graphs, name="syst_total_quad"):
    """Total systematic band: sqrt(sum_i (|w0-wi|)^2) per bin. Uses nominal x-errors."""
    out = ROOT.TGraphAsymmErrors(); ROOT.SetOwnership(out, False)
    out.SetName(name)
    for i in range(nom.GetN()):
        x0, y0 = point(nom, i)
        exl0, exh0, _, _ = errs(nom, i)
        sumsq = 0.0
        for gs in syst_graphs:
            j = find_by_x(gs, x0)
            if j < 0: continue
            _, _, eyl, eyh = errs(gs, j)
            e = max(eyl, eyh)  # they are equal by construction
            sumsq += e*e
        if sumsq <= 0.0:
            continue
        e_tot = math.sqrt(sumsq)
        p = out.GetN()
        out.SetPoint(p, x0, y0)
        out.SetPointError(p, exl0, exh0, e_tot, e_tot)
    return out

def x_range_log_safe(g):
    xmin_pos, xmax = None, None
    for i in range(g.GetN()):
        x, _ = point(g, i)
        exl, exh, _, _ = errs(g, i)
        lo = x - exl if exl < x else 0.5 * max(x, 1e-9)
        hi = x + exh
        if lo > 0:
            xmin_pos = lo if xmin_pos is None else min(xmin_pos, lo)
        if hi > 0:
            xmax = hi if xmax is None else max(xmax, hi)
    if xmin_pos is None or xmax is None or xmax <= xmin_pos:
        xmin_pos, xmax = 1e-3, 1.0
    return 0.95 * xmin_pos, 1.05 * xmax

def y_range(nom, graphs):
    ymin = None; ymax = None
    for i in range(nom.GetN()):
        _, y = point(nom, i)
        _, _, eyl, eyh = errs(nom, i)
        ymin = y - eyl if ymin is None else min(ymin, y - eyl)
        ymax = y + eyh if ymax is None else max(ymax, y + eyh)
    for g in graphs:
        for i in range(g.GetN()):
            _, y = point(g, i)
            _, _, eyl, eyh = errs(g, i)
            ymin = min(ymin, y - eyl)
            ymax = max(ymax, y + eyh)
    if ymin is None or ymax is None or ymax <= ymin:
        ymin, ymax = 0.5, 1.5
    span = ymax - ymin
    return max(0.0, ymin - 0.05*span), min(2.0, ymax + 0.05*span)

def style_nominal(g):
    g.SetLineColor(ROOT.kBlack)
    g.SetMarkerColor(ROOT.kBlack)
    g.SetMarkerStyle(20)
    g.SetLineWidth(2)

def style_syst(graphs):
    styles = [
        {"color": ROOT.kAzure+1,   "fill": 3004, "line": 2},
        {"color": ROOT.kOrange+7,  "fill": 3005, "line": 2},
        {"color": ROOT.kGreen+2,   "fill": 3351, "line": 2},
        {"color": ROOT.kMagenta+1, "fill": 3354, "line": 2},
        {"color": ROOT.kRed+1,     "fill": 1001, "alpha": 0.20, "line": 2},
    ]
    for i, g in enumerate(graphs):
        st = styles[i % len(styles)]
        g.SetLineColor(st["color"])
        g.SetLineWidth(st["line"])
        if st.get("fill", 0) == 1001:
            g.SetFillColorAlpha(st["color"], st.get("alpha", 0.25))
            g.SetFillStyle(1001)
        else:
            g.SetFillColor(st["color"])
            g.SetFillStyle(st["fill"])
        g.SetMarkerStyle(1)

def style_total_band(g):
    g.SetFillColorAlpha(ROOT.kGray+1, 0.35)
    g.SetLineColor(ROOT.kGray+2)
    g.SetLineWidth(2)
    g.SetFillStyle(1001)
    g.SetMarkerStyle(1)

def make_legend(nom, syst_graphs, labels):
    leg = ROOT.TLegend(0.58, 0.16, 0.88, 0.40)
    leg.SetBorderSize(0)
    leg.AddEntry(nom, "Nominal (w0)", "pe")
    for g, lab in zip(syst_graphs, labels):
        leg.AddEntry(g, lab, "f")
    return leg

def make_legend_total(nom, total_band):
    leg = ROOT.TLegend(0.58, 0.16, 0.88, 0.34)
    leg.SetBorderSize(0)
    leg.AddEntry(nom, "Nominal (w0)", "pe")
    leg.AddEntry(total_band, "Total syst. (quadrature)", "f")
    return leg

def main():
    if len(sys.argv) != 3:
        print("usage: python plot_syst_bands.py input.root output.pdf"); sys.exit(1)

    in_name = sys.argv[1]
    out_pdf = sys.argv[2]

    graphs = []
    missing = []
    for w in FOLDERS:
        path = os.path.join(BASE_DIR, w, in_name)
        g = get_graph(path)
        if not g: missing.append(path)
        graphs.append(g)

    if graphs[0] is None:
        print("Error: nominal graph missing:", os.path.join(BASE_DIR, FOLDERS[0], in_name))
        if missing:
            print("Also missing:", *missing[1:], sep="\n  ")
        sys.exit(2)
    if any(g is None for g in graphs[1:]):
        print("Warning: missing variations:")
        for i, g in enumerate(graphs):
            if i == 0: continue
            if g is None:
                print(f"  {BASE_DIR}/{FOLDERS[i]}/{in_name}")

    g_nom = graphs[0]
    style_nominal(g_nom)

    # Page 1: individual systematics
    syst_graphs, syst_labels = [], []
    for i in range(1, len(graphs)):
        if graphs[i] is None: continue
        gs = build_syst_graph(g_nom, graphs[i], f"syst_{FOLDERS[i]}")
        syst_graphs.append(gs)
        # syst_labels.append(f"|w0 - {FOLDERS[i]}|")
    syst_labels = ["Tight", "aco<0.01", "aco<0.03", "ZDC", "no d0"]
    style_syst(syst_graphs)

    # xmin, xmax = x_range_log_safe(g_nom)
    ymin1, ymax1 = y_range(g_nom, syst_graphs)
    xmin, xmax = 1.0, 50.0
    # ymin1, ymax1 = 0.8, 1.2

    c = ROOT.TCanvas("c", "c", 850, 720)
    c.SetLogx(True)

    c.Print(out_pdf + "[")
    frame1 = ROOT.TH1F("frame1", ";x;Scale factor", 1, xmin, xmax)
    frame1.SetDirectory(0)
    frame1.SetMinimum(ymin1); frame1.SetMaximum(ymax1)
    frame1.Draw()
    for gs in syst_graphs:
        gs.Draw("E2 SAME"); gs.Draw("E1 SAME")
    g_nom.Draw("P E1 SAME")
    leg1 = make_legend(g_nom, syst_graphs, syst_labels)
    leg1.Draw()
    c.Modified(); c.Update(); c.Print(out_pdf)

    # Page 2: quadrature-summed systematic band
    total_band = build_quadrature_band(g_nom, syst_graphs, "syst_total_quad")
    style_total_band(total_band)
    ymin2, ymax2 = y_range(g_nom, [total_band])

    c.Clear(); c.SetLogx(True)
    frame2 = ROOT.TH1F("frame2", ";x;Scale factor", 1, xmin, xmax)
    frame2.SetDirectory(0)
    frame2.SetMinimum(ymin2); frame2.SetMaximum(ymax2)
    frame2.Draw()
    total_band.Draw("E2 SAME"); total_band.Draw("E1 SAME")
    g_nom.Draw("P E1 SAME")
    leg2 = make_legend_total(g_nom, total_band)
    leg2.Draw()
    c.Modified(); c.Update(); c.Print(out_pdf)

    c.Print(out_pdf + "]")

if __name__ == "__main__":
    main()
