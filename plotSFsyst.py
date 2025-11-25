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
FOLDERS  = ["w0", "w1", "w2", "w3", "w4", "w5", "w6"]
# OBJ_NAME = "scale_factor_pT"
X_MATCH_TOL = 1e-9

def get_graph(path, eff_name):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie(): return None
    g = f.Get(eff_name)
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
        dy = abs(y0 - y1)/y0 if y0>0 else 0
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

def style_syst(graphs):
    styles = [
        {"color": ROOT.kBlack,      "line": 2,  "linestyle": 1},
        {"color": ROOT.kAzure+1,    "line": 2,  "linestyle": 2},
        {"color": ROOT.kOrange+7,   "line": 2,  "linestyle": 3},
        {"color": ROOT.kGreen+2,    "line": 2,  "linestyle": 4},
        {"color": ROOT.kMagenta+1,  "line": 2,  "linestyle": 5},
        {"color": ROOT.kRed+1,      "line": 2,  "linestyle": 6},
        {"color": ROOT.kBlue+1,     "line": 2,  "linestyle": 7},
    ]
    for i, g in enumerate(graphs):
        st = styles[i % len(styles)]
        g.SetLineColor(st["color"])
        g.SetLineWidth(st["line"])
        g.SetLineStyle(st["linestyle"])

        g.SetMarkerStyle(1)

def style_total_band(g):
    g.SetFillColorAlpha(ROOT.kGray+1, 0.35)
    g.SetLineColor(ROOT.kGray+2)
    g.SetLineWidth(2)
    g.SetFillStyle(1001)
    g.SetMarkerStyle(1)

def make_legend(graphs, labels):
    leg = ROOT.TLegend(0.58, 0.64, 0.88, 0.88)
    leg.SetBorderSize(0)
    # leg.AddEntry(graphs[0], "Nominal (w0)", "pe")
    leg.AddEntry(graphs[0], labels[0], "P E1")

    for g, lab in zip(graphs[1:], labels[1:]):
        leg.AddEntry(g, lab)
    return leg

def make_legend_total(nom, total_band):
    leg = ROOT.TLegend(0.58, 0.64, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.AddEntry(nom, "Nominal (w0)", "pe")
    leg.AddEntry(total_band, "Total syst. (quadrature)", "f")
    return leg

def graph_to_hist_step(g, name):
    """Build a TH1D with variable bins from a TGraphAsymmErrors.
       Uses x-exlow and x+exhigh as bin edges; sets bin contents to y."""
    import array as _array
    n = g.GetN()
    if n == 0: 
        print("G empty")
        return None

    # Collect per-bin (left, right, value)
    bins = []
    for i in range(n):
        x, y = point(g, i)
        exl, exh, _, _ = errs(g, i)
        left  = x - exl
        right = x + exh
        if right <= left:
            # Fallback: use midpoint spacing if x-errors are zero or bad
            # Estimate edges from neighbors
            if i == 0:
                x_next, _ = point(g, i+1)
                right = (x + x_next) / 2.0
                left  = max(1e-12, x - (right - x))  # keep >0 for log-x
            elif i == n-1:
                x_prev, _ = point(g, i-1)
                left  = (x_prev + x) / 2.0
                right = x + (x - left)
            else:
                x_prev, _ = point(g, i-1)
                x_next, _ = point(g, i+1)
                left  = (x_prev + x) / 2.0
                right = (x + x_next) / 2.0
        bins.append((left, right, y))

    # Build edges (assumes bins ordered in x)
    edges = [bins[0][0]]
    for _, r, _ in bins:
        edges.append(r)

    # Ensure strictly increasing and positive (log-x)
    for k in range(1, len(edges)):
        if edges[k] <= edges[k-1]:
            edges[k] = edges[k-1] * (1.0 + 1e-9)
        if edges[k] <= 0:
            edges[k] = 1e-12

    h = ROOT.TH1D(name, "", len(edges)-1, array('d', edges))
    h.SetDirectory(0)
    for i, (_, _, val) in enumerate(bins, start=1):
        h.SetBinContent(i, val)
        h.SetBinError(i, 0.0)  # line-only step look; keep 0 to avoid caps
    return h

def style_hist_like_graph(h, g_src):
    """Carry over line/marker styles from a graph to the histogram."""
    if h is None:
        print("Histogram is invalid")
        return
    if g_src is None:
        print("Graph is invalid")
        return
    h.SetLineColor(g_src.GetLineColor())
    h.SetLineStyle(g_src.GetLineStyle())
    h.SetLineWidth(g_src.GetLineWidth())
    h.SetMarkerStyle(1)
    h.SetFillStyle(0)


def main():
    if len(sys.argv) != 4:
        print("usage: python plot_syst_bands.py input.root output.pdf"); sys.exit(1)

    in_name = sys.argv[1]
    out_pdf = sys.argv[2]
    eff_name = sys.argv[3]
    pT = False
    if "pT" in eff_name:
        pT = True
        


    graphs = []
    missing = []
    for w in FOLDERS:
        path = os.path.join(BASE_DIR, w, in_name)
        g = get_graph(path, eff_name)
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
                return

    g_nom = graphs[0]
    # Page 1: individual systematics

    labels = ["Nominal", "Tight", "aco<0.01", "aco<0.03", "ZDC", "no d0", "pair pT<1GeV"]
    style_syst(graphs)
    
    ymin, ymax = 0.9, 1.1

    if pT:
        xmin, xmax = 1.0, 50.0
        logx = True

    else:
        xmin, xmax = -2.4, 2.4
        logx = False
        
   

    ROOT.gStyle.SetOptStat(0)
    c = ROOT.TCanvas("c", "c", 850, 720)

    c.SetLogx(logx)

    c.Print(out_pdf + "[")
    if pT:
        frame1 = ROOT.TH1F("frame1", ";p_{T} [GeV];Scale factor", 1, xmin, xmax)
    else:
        frame1 = ROOT.TH1F("frame1", r";q#eta;Scale factor", 1, xmin, xmax)
    frame1.SetDirectory(0)
    frame1.SetMinimum(ymin); frame1.SetMaximum(ymax)
    frame1.Draw()
    ROOT.gPad.Update()

    # Convert variations (graphs[1:]) to step histos and draw
    h_steps = []
    for idx, g in enumerate(graphs[1:], start=1):
        if not g: 
            h_steps.append(None)
            continue
        h = graph_to_hist_step(g, f"h_step_{idx}")
        if h is None:
            print("Histogram is invalid, possible empty graphs")
            return
        style_hist_like_graph(h, g)
        h.Draw("HIST SAME")
        h_steps.append(h)

# Nominal stays as points with errors
    g_nom.Draw("P E1 SAME")

    ROOT.gPad.RedrawAxis()
    leg1 = make_legend(graphs, labels)  # legend still refers to original graphs
    leg1.Draw()
    c.Modified(); c.Update(); c.Print(out_pdf)

    # Page 2: quadrature-summed systematic band
    syst_graphs = []
    for i in range(1, len(graphs)):
        if graphs[i] is None: continue
        gs = build_syst_graph(g_nom, graphs[i], f"syst_{FOLDERS[i]}")
        syst_graphs.append(gs)
    total_band = build_quadrature_band(g_nom, syst_graphs, "syst_total_quad")
    style_total_band(total_band)

    c.Clear(); c.SetLogx(logx)
    frame2 = ROOT.TH1F("frame2", ";x;Scale factor", 1, xmin, xmax)
    frame2.SetDirectory(0)
    frame2.SetMinimum(ymin); frame2.SetMaximum(ymax)
    frame2.Draw()
    total_band.Draw("E2 SAME");# total_band.Draw("E1 SAME")
    g_nom.Draw("P E1 SAME")
    leg2 = make_legend_total(g_nom, total_band)
    leg2.Draw()
    c.Modified(); c.Update(); c.Print(out_pdf)

    c.Print(out_pdf + "]")

if __name__ == "__main__":
    main()
