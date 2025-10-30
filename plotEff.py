#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, sys
from array import array
import ROOT
ROOT.gROOT.SetBatch(True)
from array import array

def _get_point_xy(g, i):
    # próba: bezpośrednio z buforów TGraph
    try:
        return float(g.GetPointX()[i]), float(g.GetPointY()[i])
    except Exception:
        # fallback: przez tablice 'd'
        x = array('d', [0.0]); y = array('d', [0.0])
        g.GetPoint(i, x, y)
        return float(x[0]), float(y[0])

# ------------------------ Styling ------------------------
def _set_style():
    s = ROOT.gStyle
    s.SetOptStat(0)
    s.SetTitleFont(42, "XYZ")
    s.SetLabelFont(42, "XYZ")
    s.SetTextFont(42)
    s.SetTitleSize(0.05, "XYZ")
    s.SetLabelSize(0.045, "XYZ")

    # Grid na padach + estetyka siatki
    s.SetPadGridX(True)
    s.SetGridColor(ROOT.kGray+1)
    s.SetGridStyle(3)      # lekko kreskowana
    s.SetGridWidth(1)

    s.SetPadLeftMargin(0.12); s.SetPadRightMargin(0.04); s.SetPadBottomMargin(0.12)
    s.SetPadTickX(1); s.SetPadTickY(1)


# ------------------------ Helpers ------------------------
def _parse_bins(bins_str):
    edges = [float(x) for x in bins_str.split(",")]
    if len(edges) < 2: raise ValueError("Need ≥2 bin edges.")
    if sorted(edges) != edges: raise ValueError("Bin edges must be strictly increasing.")
    return array("d", edges)

def _get_obj_recursive(tfile, name):
    obj = tfile.Get(name)
    if obj: return obj
    def walk_dir(d):
        for key in d.GetListOfKeys():
            o = key.ReadObj()
            if o.InheritsFrom("TH1") and key.GetName() == name:
                return o
            if o.InheritsFrom("TDirectory"):
                fnd = walk_dir(o)
                if fnd: return fnd
        return None
    return walk_dir(tfile)

def _open_hist(path, hname):
    f = ROOT.TFile.Open(path, "READ")
    if not f or f.IsZombie(): raise IOError(f"Cannot open file: %s" % path)
    h = _get_obj_recursive(f, hname)
    if not h or not h.InheritsFrom("TH1"):
        f.Close()
        raise KeyError("Histogram '%s' not found in %s" % (hname, path))
    hc = h.Clone(h.GetName() + "__clone")
    hc.SetDirectory(0)
    if not hc.GetSumw2N(): hc.Sumw2()
    f.Close()
    return hc

def _overlap(a1, a2, b1, b2):
    lo = max(a1, b1); hi = min(a2, b2)
    return max(0.0, hi - lo)

def _variable_rebin_by_overlap(h, new_edges):
    nb_new = len(new_edges)-1
    out = ROOT.TH1D(h.GetName() + "__varrebin", h.GetTitle(), nb_new, new_edges)
    out.Sumw2()

    xax = h.GetXaxis()
    nb_old = h.GetNbinsX()
    old = []
    for i in range(1, nb_old+1):
        lo = xax.GetBinLowEdge(i)
        hi = xax.GetBinUpEdge(i)
        c  = h.GetBinContent(i)
        e2 = (h.GetBinError(i))**2
        old.append((lo, hi, c, e2))

    for j in range(1, nb_new+1):
        nlo = new_edges[j-1]; nhi = new_edges[j]
        csum = 0.0; e2sum = 0.0
        for (lo, hi, c, e2) in old:
            ov = _overlap(nlo, nhi, lo, hi)
            if ov <= 0: continue
            frac = ov / (hi - lo) if hi > lo else 0.0
            csum  += frac * c
            e2sum += (frac*frac) * e2
        out.SetBinContent(j, csum)
        out.SetBinError(j, e2sum**0.5)

    out.SetDirectory(0)
    return out

def _make_efficiency(h_pass, h_total, name):
    if not ROOT.TEfficiency.CheckConsistency(h_pass, h_total):
        raise ValueError("Inconsistent pass/total for %s" % name)
    eff = ROOT.TEfficiency(h_pass, h_total)
    # For weighted inputs ROOT auto-detects and uses normal approximation.
    # Keep kFNormal as a sensible default (works for both weighted/unweighted).
    eff.SetStatisticOption(ROOT.TEfficiency.kFNormal)
    eff.SetName(name)
    return eff

def _eff_to_graph(eff, title, marker_style, line_color):
    g = eff.CreateGraph()
    if not g: return None
    g.SetTitle(title)
    g.SetMarkerStyle(marker_style); g.SetMarkerSize(1.2)
    g.SetMarkerColor(line_color);   g.SetLineColor(line_color); g.SetLineWidth(2)
    return g

def _product_graph(effA, effB, name, title, marker_style, line_color, new_edges):
    nb = len(new_edges)-1
    g = ROOT.TGraphErrors(nb); g.SetName(name); g.SetTitle(title)
    g.SetMarkerStyle(marker_style); g.SetMarkerSize(1.2)
    g.SetMarkerColor(line_color);   g.SetLineColor(line_color); g.SetLineWidth(2)

    for i in range(1, nb+1):
        x  = 0.5*(new_edges[i-1] + new_edges[i])
        ex = 0.5*(new_edges[i]   - new_edges[i-1])

        a = effA.GetEfficiency(i); b = effB.GetEfficiency(i)
        sa = 0.5*(effA.GetEfficiencyErrorUp(i) + effA.GetEfficiencyErrorLow(i))
        sb = 0.5*(effB.GetEfficiencyErrorUp(i) + effB.GetEfficiencyErrorLow(i))
        prod = a*b
        sp   = 0.0
        if a>0 and b>0:
            sp = abs(prod)*(((sa/a)**2 + (sb/b)**2)**0.5)
        g.SetPoint(i-1, x, prod)
        g.SetPointError(i-1, ex, sp)
    return g

def _ratio_graph(eff_data, eff_mc, name, title, marker_style, line_color, new_edges):
    nb = len(new_edges)-1
    g = ROOT.TGraphErrors(nb); g.SetName(name); g.SetTitle(title)
    g.SetMarkerStyle(marker_style); g.SetMarkerSize(1.0)
    g.SetMarkerColor(line_color);   g.SetLineColor(line_color); g.SetLineWidth(2)

    for i in range(1, nb+1):
        x  = 0.5*(new_edges[i-1] + new_edges[i])
        ex = 0.5*(new_edges[i]   - new_edges[i-1])

        a  = eff_data.GetEfficiency(i)
        b  = eff_mc  .GetEfficiency(i)
        sa = 0.5*(eff_data.GetEfficiencyErrorUp(i) + eff_data.GetEfficiencyErrorLow(i))
        sb = 0.5*(eff_mc  .GetEfficiencyErrorUp(i) + eff_mc  .GetEfficiencyErrorLow(i))

        r  = a/b if (b>0) else 0.0
        sr = 0.0
        if a>0 and b>0:
            sr = abs(r)*(((sa/a)**2 + (sb/b)**2)**0.5)

        g.SetPoint(i-1, x, r)
        g.SetPointError(i-1, ex, sr)
    return g

def _multiply_ratio_graphs(g1, g2, name, title):
    n = min(g1.GetN(), g2.GetN())
    out = ROOT.TGraphErrors(n); out.SetName(name); out.SetTitle(title)
    out.SetMarkerStyle(20); out.SetMarkerSize(1.0)
    out.SetMarkerColor(ROOT.kBlack); out.SetLineColor(ROOT.kBlack); out.SetLineWidth(2)

    for i in range(n):
        x1, y1 = _get_point_xy(g1, i)
        x2, y2 = _get_point_xy(g2, i)
        x = 0.5*(x1 + x2)
        r = y1 * y2

        ex1 = g1.GetErrorX(i); ey1 = g1.GetErrorY(i)
        ex2 = g2.GetErrorX(i); ey2 = g2.GetErrorY(i)
        ex  = max(ex1, ex2)
        er  = 0.0
        if y1 != 0.0 and y2 != 0.0:
            er = abs(r) * ((ey1/abs(y1))**2 + (ey2/abs(y2))**2)**0.5

        out.SetPoint(i, x, r)
        out.SetPointError(i, ex, er)
    return out



def _draw_comp_page(pdf, x_title, title, g_data, g_mc, new_edges,
                    y_min=0.0, y_max=1.05, logx=True):
    if (g_data is None or g_data.GetN()==0) and (g_mc is None or g_mc.GetN()==0):
        print(f"[note] Skipping page: '{title}' (no points to draw)")
        return False

    c = ROOT.TCanvas("c","",900,700)
    c.SetGridx(True); c.SetGridy(True)
    if logx:
        c.SetLogx(True)

    # ensure xmin>0 for log-x
    xmin = float(new_edges[0]); xmax = float(new_edges[-1])
    if logx and xmin <= 0.0:
        xmin_pos = next((float(e) for e in new_edges if e > 0.0), None)
        if xmin_pos is None:
            raise ValueError("Log-x requested but no positive bin edges found.")
        print(f"[warn] log-x: adjusted x-min to first positive edge: {xmin_pos}")
        xmin = xmin_pos

    frame = ROOT.TH1F("frame","",100, xmin, xmax)
    frame.SetDirectory(0)
    frame.SetTitle(title)
    frame.GetXaxis().SetTitle(x_title)
    frame.GetYaxis().SetTitle("Efficiency")
    frame.GetYaxis().SetRangeUser(0.7, y_max)
    frame.Draw("AXIS")

    # axis cosmetics (ROOT-version friendly)
    if logx:
        ax = frame.GetXaxis()
        try: ax.SetMoreLogLabels(True)
        except Exception: pass
        try: ax.SetNoExponent(True)
        except Exception: pass
        try: ROOT.TGaxis.SetMaxDigits(3)   # reduce exponent clutter
        except Exception: pass

    # y = 1 reference line
    yref = 1.0
    yline = ROOT.TLine(xmin, yref, xmax, yref)
    yline.SetLineStyle(2); yline.SetLineWidth(2); yline.SetLineColor(ROOT.kGray+2)
    yline.Draw("SAME")

    if not hasattr(c, "_keep"): c._keep = []
    c._keep.extend([frame, yline])

    if g_mc and g_mc.GetN()>0:     g_mc.Draw("P SAME")
    if g_data and g_data.GetN()>0: g_data.Draw("P SAME")

    leg = ROOT.TLegend(0.64, 0.18, 0.94, 0.30)
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextFont(42)
    if g_data and g_data.GetN()>0: leg.AddEntry(g_data, "Data", "pe")
    if g_mc   and g_mc.GetN()>0:   leg.AddEntry(g_mc,   "MC",   "pe")
    if leg.GetNRows()>0: leg.Draw()

    pave = ROOT.TPaveText(0.14, 0.92, 0.95, 0.995, "NDC")
    pave.SetFillStyle(0); pave.SetBorderSize(0); pave.SetTextFont(42); pave.SetTextSize(0.035)
    pave.AddText(title); pave.Draw()

    c.Print(pdf); c.Close()
    return True

def _draw_comp_page_with_ratio(pdf, x_title, title,
                               g_data, g_mc, g_ratio, new_edges,
                               y_min=0.0, y_max=1.05,
                               ratio_min=None, ratio_max=None,
                               logx=True):
    if (g_data is None or g_data.GetN()==0) and (g_mc is None or g_mc.GetN()==0):
        print(f"[note] Skipping page: '{title}' (no points to draw)")
        return False

    c = ROOT.TCanvas("c","",900,800)

    # --- Pads ---
    top = ROOT.TPad("top","",0,0.32,1,1);     top.SetBottomMargin(0.04)
    bot = ROOT.TPad("bot","",0,0.00,1,0.32);  bot.SetTopMargin(0.03); bot.SetBottomMargin(0.36)
    for p in (top, bot):
        p.SetLeftMargin(0.12); p.SetRightMargin(0.04)
        p.SetGridx(True); p.SetGridy(True)
        if logx: p.SetLogx(True)
    top.Draw(); bot.Draw()

    xmin = float(new_edges[0]); xmax = float(new_edges[-1])
    if logx and xmin <= 0.0:
        xmin_pos = next((float(e) for e in new_edges if e > 0.0), None)
        if xmin_pos is None:
            raise ValueError("Log-x requested but no positive bin edges found.")
        print(f"[warn] log-x: adjusted x-min to first positive edge: {xmin_pos}")
        xmin = xmin_pos

    # --- TOP: efficiencies ---
    top.cd()
    frame = ROOT.TH1F("frame","",100, xmin, xmax)
    frame.SetDirectory(0)
    frame.SetTitle(title)
    frame.GetXaxis().SetTitle("")                 # tytuł x tylko na dole
    frame.GetXaxis().SetLabelSize(0)              # bez cyfr na górnym panelu
    frame.GetYaxis().SetTitle("Efficiency")
    frame.GetYaxis().SetRangeUser(0.7, y_max)
    frame.Draw("AXIS")

    if logx:
        ax = frame.GetXaxis()
        try: ax.SetMoreLogLabels(True)
        except Exception: pass
        try: ax.SetNoExponent(True)
        except Exception: pass
        try: ROOT.TGaxis.SetMaxDigits(3)
        except Exception: pass

    yline_top = ROOT.TLine(xmin, 1.0, xmax, 1.0)
    yline_top.SetLineStyle(2); yline_top.SetLineWidth(2); yline_top.SetLineColor(ROOT.kGray+2)
    yline_top.Draw("SAME")

    if g_mc and g_mc.GetN()>0:     g_mc.Draw("P SAME")
    if g_data and g_data.GetN()>0: g_data.Draw("P SAME")

    leg = ROOT.TLegend(0.64, 0.18, 0.94, 0.30)
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextFont(42)
    if g_data and g_data.GetN()>0: leg.AddEntry(g_data, "Data", "pe")
    if g_mc   and g_mc.GetN()>0:   leg.AddEntry(g_mc,   "MC",   "pe")
    if leg.GetNRows()>0: leg.Draw()

    pave = ROOT.TPaveText(0.14, 0.92, 0.95, 0.995, "NDC")
    pave.SetFillStyle(0); pave.SetBorderSize(0); pave.SetTextFont(42); pave.SetTextSize(0.035)
    pave.AddText(title); pave.Draw()

    # --- BOT: ratio ---
    bot.cd()
    # auto zakres jeśli nie podano
    if g_ratio and g_ratio.GetN()>0 and (ratio_min is None or ratio_max is None):
        ys = []
        for i in range(g_ratio.GetN()):
            _, y = _get_point_xy(g_ratio, i)
            if y != 0.0 and abs(y) < 10:
                ys.append(y)

        if ys:
            lo, hi = min(ys), max(ys)
            pad = 0.15*(hi-lo if hi>lo else 1.0)
            lo = min(lo, 1.0); hi = max(hi, 1.0)
            ratio_min = (lo - pad) if ratio_min is None else ratio_min
            ratio_max = (hi + pad) if ratio_max is None else ratio_max
    if ratio_min is None: ratio_min = 0.8
    if ratio_max is None: ratio_max = 1.2

    rframe = ROOT.TH1F("rframe","",100, xmin, xmax)
    rframe.SetDirectory(0)
    rframe.SetTitle("")
    rframe.GetXaxis().SetTitle(x_title)
    rframe.GetYaxis().SetTitle("Data/MC")
    rframe.GetYaxis().SetNdivisions(505, True)
    rframe.GetYaxis().SetTitleSize(0.10)
    rframe.GetYaxis().SetLabelSize(0.09)
    rframe.GetXaxis().SetTitleSize(0.11)
    rframe.GetXaxis().SetLabelSize(0.10)
    rframe.GetYaxis().SetRangeUser(ratio_min, ratio_max)
    rframe.Draw("AXIS")

    yline_bot = ROOT.TLine(xmin, 1.0, xmax, 1.0)
    yline_bot.SetLineStyle(2); yline_bot.SetLineWidth(2); yline_bot.SetLineColor(ROOT.kGray+2)
    yline_bot.Draw("SAME")

    if g_ratio and g_ratio.GetN()>0:
        g_ratio.Draw("P SAME")

    if not hasattr(c, "_keep"): c._keep = []
    c._keep.extend([frame, yline_top, leg, pave, rframe, yline_bot, g_ratio, g_data, g_mc])

    c.Print(pdf); c.Close()
    return True



# ------------------------ Main generator ------------------------
def genEff(id_ms_data, id_ms_mc, mu_id_data, mu_id_mc, bins, out_pdf="efficiency_plots.pdf",
           hist_pass="eps_pass", hist_total="eps_total", x_title="Variable"):
    """
    Build 3-page PDF:
      1) ID_MS: Data vs MC efficiency
      2) mu_ID: Data vs MC efficiency
      3) Product (ID_MS × mu_ID): Data vs MC
    """
    _set_style()
    edges = _parse_bins(bins) if isinstance(bins, str) else array("d", bins)
    print("Making efficiency plots")

    # Load originals
    h_idms_d_pass  = _open_hist(id_ms_data, hist_pass)
    h_idms_d_total = _open_hist(id_ms_data, hist_total)
    h_idms_m_pass  = _open_hist(id_ms_mc,   hist_pass)
    h_idms_m_total = _open_hist(id_ms_mc,   hist_total)

    h_muid_d_pass  = _open_hist(mu_id_data, hist_pass)
    h_muid_d_total = _open_hist(mu_id_data, hist_total)
    h_muid_m_pass  = _open_hist(mu_id_mc,   hist_pass)
    h_muid_m_total = _open_hist(mu_id_mc,   hist_total)

    # Variable rebin (overlap-based)
    idms_d_pass   = _variable_rebin_by_overlap(h_idms_d_pass,  edges)
    idms_d_total  = _variable_rebin_by_overlap(h_idms_d_total, edges)
    idms_m_pass   = _variable_rebin_by_overlap(h_idms_m_pass,  edges)
    idms_m_total  = _variable_rebin_by_overlap(h_idms_m_total, edges)

    muid_d_pass   = _variable_rebin_by_overlap(h_muid_d_pass,  edges)
    muid_d_total  = _variable_rebin_by_overlap(h_muid_d_total, edges)
    muid_m_pass   = _variable_rebin_by_overlap(h_muid_m_pass,  edges)
    muid_m_total  = _variable_rebin_by_overlap(h_muid_m_total, edges)

    # Efficiencies
    eff_idms_data = _make_efficiency(idms_d_pass, idms_d_total, "eff_idms_data")
    eff_idms_mc   = _make_efficiency(idms_m_pass, idms_m_total, "eff_idms_mc")
    eff_muid_data = _make_efficiency(muid_d_pass, muid_d_total, "eff_muid_data")
    eff_muid_mc   = _make_efficiency(muid_m_pass, muid_muid_total, "eff_muid_mc") if False else _make_efficiency(muid_m_pass, muid_m_total, "eff_muid_mc")

    # Graphs
    col_data = ROOT.kBlack; col_mc = ROOT.kAzure+2
    g_idms_data = _eff_to_graph(eff_idms_data, f"ID_MS efficiency;{x_title};Efficiency", 20, col_data)
    g_idms_mc   = _eff_to_graph(eff_idms_mc,   f"ID_MS efficiency;{x_title};Efficiency", 24, col_mc)
    g_muid_data = _eff_to_graph(eff_muid_data, f"mu_ID efficiency;{x_title};Efficiency", 20, col_data)
    g_muid_mc   = _eff_to_graph(eff_muid_mc,   f"mu_ID efficiency;{x_title};Efficiency", 24, col_mc)

    # Product
    g_prod_data = _product_graph(eff_idms_data, eff_muid_data, "prod_data",
                                 f"Combined efficiency: ID_MS × mu_ID;{x_title};Efficiency",
                                 20, col_data, edges)
    g_prod_mc   = _product_graph(eff_idms_mc,   eff_muid_mc,   "prod_mc",
                                 f"Combined efficiency: ID_MS × mu_ID;{x_title};Efficiency",
                                 24, col_mc, edges)

    # --- Ratio graphs ---
    r_idms = _ratio_graph(eff_idms_data, eff_idms_mc,
                        "ratio_idms", f"ID_MS ratio;{x_title};Data/MC", 20, ROOT.kBlack, edges)
    r_muid = _ratio_graph(eff_muid_data, eff_muid_mc,
                        "ratio_muid", f"mu_ID ratio;{x_title};Data/MC", 20, ROOT.kBlack, edges)
    # Product ratio = (ID_MS ratio) × (mu_ID ratio)
    r_prod = _multiply_ratio_graphs(r_idms, r_muid,
                                    "ratio_prod", f"Product ratio;{x_title};Data/MC")

    # Output PDF
    opener = ROOT.TCanvas(); opener.Print(out_pdf + "["); opener.Close()
    pages = 0
    pages += _draw_comp_page_with_ratio(out_pdf, x_title, "ID_MS: Data vs MC",
                                        g_idms_data, g_idms_mc, r_idms, edges)
    pages += _draw_comp_page_with_ratio(out_pdf, x_title, "mu_ID: Data vs MC",
                                        g_muid_data, g_muid_mc, r_muid, edges)
    pages += _draw_comp_page_with_ratio(out_pdf, x_title, "Product (ID_MS x mu_ID): Data vs MC",
                                        g_prod_data, g_prod_mc, r_prod, edges)
    closer = ROOT.TCanvas(); closer.Print(out_pdf + "]"); closer.Close()
    if pages == 0:
        print("[warn] No pages produced (no non-empty graphs). Check inputs and binning.")
    else:
        print(f"[ok] Saved: {out_pdf}")

# ------------------------ CLI wrapper ------------------------
def _cli():
    ap = argparse.ArgumentParser(description="Generate efficiency comparison plots (Data vs MC) for ID_MS and mu_ID, plus product.")
    ap.add_argument("--id-ms-data", required=True)
    ap.add_argument("--id-ms-mc",   required=True)
    ap.add_argument("--mu-id-data", required=True)
    ap.add_argument("--mu-id-mc",   required=True)
    ap.add_argument("--hist-pass",  default="eps_pass")
    ap.add_argument("--hist-total", default="eps_total")
    ap.add_argument("--bins",       required=True)
    ap.add_argument("--out",        default="./histograms/efficiency.pdf")
    ap.add_argument("--x-title",    default="Variable")
    args = ap.parse_args()
    try:
        genEff(args.id_ms_data, args.id_ms_mc, args.mu_id_data, args.mu_id_mc,
               args.bins, out_pdf=args.out,
               hist_pass=args.hist_pass, hist_total=args.hist_total,
               x_title=args.x_title)
    except Exception as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    _cli()
