import ROOT
import sys
from array import array
import os
import math

# ------------- 2D histograms -------------
def add_cut_lines(
    hist,
    x_cuts=None,
    y_cuts=None,
    color=ROOT.kRed,
    style=2,
    width=2
):
    """
    Draw red dashed cut lines on a histogram (already drawn).

    Returns a list of TLine objects so they don't get garbage-collected.
    """
    if x_cuts is None:
        x_cuts = []
    if y_cuts is None:
        y_cuts = []

    xmin = hist.GetXaxis().GetXmin()
    xmax = hist.GetXaxis().GetXmax()
    ymin = hist.GetYaxis().GetXmin()
    ymax = hist.GetYaxis().GetXmax()

    lines = []

    for xc in x_cuts:
        line = ROOT.TLine(xc, ymin, xc, ymax)
        line.SetLineColor(color)
        line.SetLineStyle(style)
        line.SetLineWidth(width)
        line.Draw("SAME")
        lines.append(line)

    for yc in y_cuts:
        line = ROOT.TLine(xmin, yc, xmax, yc)
        line.SetLineColor(color)
        line.SetLineStyle(style)
        line.SetLineWidth(width)
        line.Draw("SAME")
        lines.append(line)

    ROOT.gPad.Update()
    return lines

#
def draw_2d_hist(
    h2,
    canvas_size,
    x_label="X",
    y_label="Y",
    z_label="",
    title_text="",
    canvas_name="c2d",
    logz=False,
    logx=False,
    text_ndc_pos=(0.15, 0.93),
    text = False,
    tight_layout = False
):
    c = ROOT.TCanvas(canvas_name, canvas_name, canvas_size[0], canvas_size[1])

    c.SetLeftMargin(0.13)
    c.SetRightMargin(0.14)
    c.SetBottomMargin(0.15)
    c.SetTopMargin(0.05)

    if logz:
        c.SetLogz()

    ROOT.gStyle.SetOptStat(0)
    if text:
        h2.Scale(100)
        
    h2.SetStats(0)
    h2.SetTitle("")
    h2.GetXaxis().SetTitle(x_label)
    h2.GetYaxis().SetTitle(y_label)
    h2.GetZaxis().SetTitle(z_label)
    if z_label:
        h2.GetZaxis().SetTitle(z_label)

    h2.GetXaxis().SetTitleSize(0.045)
    h2.GetYaxis().SetTitleSize(0.045)
    h2.GetZaxis().SetTitleSize(0.045)

    drawopt = "COLZ"
    if text:
        ROOT.gStyle.SetPaintTextFormat('4.1f')
        drawopt = "COLZ TEXT"
        h2.GetXaxis().SetTickLength(0.0)
        h2.GetYaxis().SetTickLength(0.0)
    c.SetLogx(logx)
    h2.Draw(drawopt)
    if logx:
        h2.GetXaxis().SetMoreLogLabels(True)
        h2.GetXaxis().SetNoExponent(True)
        h2.GetXaxis().SetRangeUser(3, 50)
    
    if tight_layout:
        c.SetLeftMargin(0.10)
        h2.GetYaxis().SetTitleOffset(0.3)

        min, max = h2.GetMinimum(), h2.GetMaximum()
        h2.SetMinimum(min-0.02)
        ROOT.gStyle.SetNumberContours(255)
        ROOT.gROOT.ForceStyle()  
        h2.SetContour(255)

    if title_text:
        latex = ROOT.TLatex()
        latex.SetNDC(True)
        latex.SetTextSize(0.04)
        latex.DrawLatex(text_ndc_pos[0], text_ndc_pos[1], title_text)

    c.Update()
    return c

#
def plot_2d_histogram(
        *,in_fname,
        h2_name,
        x_label = "",
        y_label = "",
        z_label = "",
        logz = False,
        logx = False,
        x_cuts = None,
        y_cuts = None,
        text = False,
        tight_layout = False,
        pdf_name,
        canvas_size=(800,600)

):
    f = ROOT.TFile(in_fname)
    h2 = f.Get(h2_name)
    c = draw_2d_hist(
        h2 = h2,
        x_label=x_label,
        y_label=y_label,
        z_label=z_label,
        logz=logz,
        logx=logx,
        text=text,
        tight_layout=tight_layout,
        canvas_size=canvas_size
    )

    lines = add_cut_lines(
        hist = h2,
        x_cuts = x_cuts,
        y_cuts = y_cuts
    )
    c.Print(pdf_name)
    f.Close()


# ------------- 1D histograms -------------
def get_hist(tfile, name):
    h = tfile.Get(name)
    if not h:
        return None
    h = h.Clone(name + "_clone")
    h.SetDirectory(0)
    if not h.GetSumw2N():
        h.Sumw2()
    return h

#
def style_h_datahist(h):
    h.SetMarkerStyle(20)
    h.SetMarkerSize(0.9)
    h.SetMarkerColor(ROOT.kBlack)
    h.SetLineColor(ROOT.kBlack)
    h.SetLineWidth(2)

#
def style_h_mchist(h):
    h.SetLineColor(ROOT.kAzure + 2)
    h.SetLineWidth(2)
    h.SetFillColorAlpha(ROOT.kAzure + 1, 0.35)


def make_ratio(data, mc):
    """Return (ratio_hist, mc_uncertainty_band TGraphErrors). Ratio = Data/MC."""
    ratio = data.Clone(data.GetName() + "_ratio")
    nb = ratio.GetNbinsX()

    x = []
    y = []
    ex = []
    ey = []

    for i in range(1, nb + 1):
        D  = data.GetBinContent(i)
        M  = mc.GetBinContent(i)
        eD = data.GetBinError(i)
        eM = mc.GetBinError(i)

        if M > 0.0:
            r = D / M
            if D > 0.0:
                rel = (eD / D) ** 2 + (eM / M) ** 2
                er  = r * (rel ** 0.5)
            else:
                er = 0.0
        else:
            r, er = 0.0, 0.0

        ratio.SetBinContent(i, r)
        ratio.SetBinError(i, er)

        x.append(mc.GetXaxis().GetBinCenter(i))
        y.append(1.0)
        ex.append(0.5 * mc.GetXaxis().GetBinWidth(i))
        ey.append(eM / M if M > 0.0 else 0.0)

    band = ROOT.TGraphErrors(nb)
    for i in range(nb):
        band.SetPoint(i, x[i], y[i])
        band.SetPointError(i, ex[i], ey[i])

    band.SetFillColorAlpha(ROOT.kGray + 1, 0.35)
    band.SetLineColor(ROOT.kGray + 2)
    band.SetMarkerStyle(0)

    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetYaxis().SetTitleSize(0.11)
    ratio.GetYaxis().SetLabelSize(0.10)
    ratio.GetXaxis().SetLabelSize(0.10)
    ratio.GetXaxis().SetTitleSize(0.12)
    ratio.GetXaxis().SetTitleOffset(1.0)
    ratio.SetMarkerStyle(20)
    ratio.SetMarkerSize(0.8)
    ratio.SetLineColor(ROOT.kBlack)
    ratio.SetMarkerColor(ROOT.kBlack)

    return ratio, band


def draw_one_h1d(canvas, h_data, h_mc, title, ylim_ratio, logy=False, cut:float|None=None):
    RATIO_YMIN, RATIO_YMAX = ylim_ratio
    canvas.Clear()
    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.30, 1, 1.00)
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.30)
    pad1.SetBottomMargin(0.02)
    pad2.SetTopMargin(0.03)
    pad2.SetBottomMargin(0.35)
    pad1.Draw()
    pad2.Draw()
    pad2.SetGrid(True)

    pad1.cd()
    if logy:
        pad1.SetLogy()

    style_h_mchist(h_mc)
    style_h_datahist(h_data)

    h_mc.SetTitle(title)
    h_data.SetTitle(title)

    h_mc.Draw("HIST")
    h_data.Draw("E1 SAME")

    max_y = max(h_mc.GetMaximum(), h_data.GetMaximum())
    if logy:
        h_mc.SetMinimum(0.1)
        h_mc.SetMaximum(max_y * 10.0)
    else:
        h_mc.SetMinimum(0.0)
        h_mc.SetMaximum(max_y * 1.35)

    h_mc.GetXaxis().SetLabelSize(0)
    h_mc.GetYaxis().SetTitleSize(0.04)

    ROOT.gStyle.SetOptStat(0)

    leg = ROOT.TLegend(0.60, 0.72, 0.88, 0.89)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h_data, "Data 2023", "lep")
    leg.AddEntry(h_mc,   "SuperChic #gamma#gamma#rightarrow#mu^{+}#mu^{-}", "f")
    leg.Draw()

    pad1.Modified()
    pad1.Update()

    cut_line = None
    if cut is not None:
        ymin = pad1.GetUymin()
        ymax = pad1.GetUymax()
        if logy:
            ymax = 10**ymax
        cut_line = ROOT.TLine(cut, ymin, cut, ymax)
        cut_line.SetLineColor(ROOT.kRed)
        cut_line.SetLineStyle(2)
        cut_line.SetLineWidth(2)
        cut_line.Draw("SAME")
    pad2.cd()
    ratio, band = make_ratio(h_data, h_mc)
    ratio.GetYaxis().SetRangeUser(RATIO_YMIN, RATIO_YMAX)

    frame = pad2.DrawFrame(
        h_data.GetXaxis().GetXmin(), RATIO_YMIN,
        h_data.GetXaxis().GetXmax(), RATIO_YMAX
    )
    frame.GetYaxis().SetTitle("Data/MC")
    frame.GetYaxis().SetNdivisions(505)
    frame.GetYaxis().SetTitleSize(0.11)
    frame.GetYaxis().SetTitleOffset(0.45)
    frame.GetYaxis().SetLabelSize(0.10)
    frame.GetXaxis().SetTitle(h_data.GetXaxis().GetTitle())
    frame.GetXaxis().SetTitleSize(0.12)
    frame.GetXaxis().SetLabelSize(0.10)

    ratio.Draw("E1 SAME")


    line = ROOT.TLine(h_data.GetXaxis().GetXmin(), 1.0,
                      h_data.GetXaxis().GetXmax(), 1.0)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kRed)
    line.Draw("SAME")
    if not hasattr(canvas, "keep"):
        canvas.keep = []
    objs = [leg, band, ratio, line, pad1, pad2]
    if cut_line is not None:
        objs.append(cut_line)
    canvas.keep.extend(objs)
    canvas.Update()


def plot_1d_histogram(
        *,
        data_fname:str,
        mc_fname:str,
        output_pdf:str,
        h_name:str,
        cut = None,
        canvas_size=(800, 600),
        logy = False,
        title = '',
        xlabel = '',
        ylabel = '',
        ylim_ratio = (0.5, 1.5)
):
    f_data = ROOT.TFile.Open(data_fname, "READ")
    f_mc   = ROOT.TFile.Open(mc_fname,   "READ")
    if not f_data or f_data.IsZombie():
        sys.exit(f"ERROR: cannot open data file: {data_fname}")
    if not f_mc or f_mc.IsZombie():
        sys.exit(f"ERROR: cannot open MC file: {mc_fname}")

    c = ROOT.TCanvas("c", "c", canvas_size[0], canvas_size[1])

    h_data = get_hist(f_data, h_name)
    h_mc   = get_hist(f_mc,   h_name)

    if h_data is None:
        print(f"[WARN] Data histogram '{h_name}' not found, skipping.")
        return
    if h_mc is None:
        print(f"[WARN] MC histogram '{h_name}' not found, skipping.")
        return

    full_desc = title+';'+xlabel+';'+ylabel
    h_data.SetTitle(title)
    draw_one_h1d(c, h_data, h_mc, full_desc, ylim_ratio, logy=logy, cut=cut)

    c.Print(output_pdf)

    f_data.Close()
    f_mc.Close()
    print(f"Saved: {output_pdf}")



# ------------- efficiency plots -------------

def info_text(*, xpos = 0.2, ypos = 0.8, pt_variant = True):
        txt = ROOT.TLatex()
        txt.SetNDC(True)
        txt.SetTextSize(0.04)
        if pt_variant:
            txt.DrawLatex(xpos, ypos, "#splitline{#sqrt{s_{NN}} = 5.36 TeV}{-2.4 < #it{#eta} < 2.4}")
        else:
            txt.DrawLatex(xpos, ypos, "#splitline{#sqrt{s_{NN}} = 5.36 TeV}{3 GeV < #it{p}_{T} < 50 GeV}")



def ratio_of_TEff(e1, e2):
    g = ROOT.TGraphAsymmErrors(); ROOT.SetOwnership(g, False)
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
    g = ROOT.TGraphAsymmErrors(); ROOT.SetOwnership(g, False)
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
    o.SetLineColor(color)
    o.SetMarkerColor(color)
    o.SetMarkerStyle(marker)
    o.SetLineWidth(2)


def draw_one_eff(canvas, data_obj, mc_obj, title, xlabel, ylabel, ylim, ylim_ratio, logx=False):
    canvas.Clear(); canvas.Divide(1, 2)
    is_eff = data_obj.InheritsFrom("TEfficiency")
    xmin, xmax = -2.4, 2.4
    if logx:
        xmin, xmax = 3, 50
    pad1 = canvas.cd(1)
    pad1.SetPad(0, 0.30, 1, 1)
    pad1.SetBottomMargin(0.02)
    if(logx):
        pad1.SetLogx()
    ymin, ymax = ylim
    ymin_ratio, ymax_ratio = ylim_ratio
    frame_top = pad1.DrawFrame(xmin, ymin, xmax, ymax)
    frame_top.SetTitle(f"{title};{xlabel};{ylabel}")
    frame_top.GetXaxis().SetLabelSize(0)
    frame_top.GetXaxis().SetTitleSize(0)

    style_obj(data_obj, ROOT.kBlack, 20)
    style_obj(mc_obj,   ROOT.kRed + 1, 24)
    data_obj.Draw("P SAME")
    mc_obj.Draw("P SAME")
    info_text(xpos = 0.2, ypos = 0.2, pt_variant=logx)

    leg = ROOT.TLegend(0.60, 0.70, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.AddEntry(data_obj, "Data 2023", "pe")
    leg.AddEntry(mc_obj,   "SuperChic #gamma#gamma#rightarrow#mu^{+}#mu^{-}",   "pe")
    leg.Draw()

    pad2 = canvas.cd(2)
    pad2.SetPad(0, 0, 1, 0.30)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.35)
    if logx:
        pad2.SetLogx()

    frame_bot = pad2.DrawFrame(xmin, ymin_ratio, xmax, ymax_ratio)
    xaxis_bot = frame_bot.GetXaxis()
    yaxis_bot = frame_bot.GetYaxis()

    xaxis_bot.SetTitle(xlabel)
    yaxis_bot.SetTitle("Data/MC")
    yaxis_bot.SetNdivisions(505)
    xaxis_bot.SetTitleSize(0.11)
    yaxis_bot.SetTitleSize(0.11)
    xaxis_bot.SetLabelSize(0.10)
    yaxis_bot.SetLabelSize(0.10)
    yaxis_bot.SetTitleOffset(0.45)
    xaxis_bot.SetTitleOffset(1.2)

    if logx:
        xaxis_bot.SetMoreLogLabels(True)
        xaxis_bot.SetNoExponent(True)
        pad2.SetTicks(1, 1)

    one = ROOT.TLine(xmin, 1.0, xmax, 1.0)
    one.SetLineColor(ROOT.kRed)
    one.SetLineWidth(2)
    one.SetLineStyle(2)
    one.Draw()

    gr = ratio_of_TEff(data_obj, mc_obj) if is_eff else ratio_of_TGraphs(data_obj, mc_obj)
    style_obj(gr, ROOT.kBlack, 20)
    gr.Draw("P SAME")
    if not hasattr(canvas, "keep"):
        canvas.keep = []
    canvas.keep.extend([one, leg])
    canvas.Modified()
    canvas.Update()

def plot_efficiency( *,
        data_fname:str,
        mc_fname:str,
        output_pdf:str,
        obj_name:str,
        canvas_size=[800, 600],
        logx = False,
        title = '',
        xlabel = '',
        ylabel = '',
        ylim = (0.7, 1.1),
        ylim_ratio = (0.93, 1.07)
):
    fD = ROOT.TFile.Open(data_fname)
    fM = ROOT.TFile.Open(mc_fname)

    if not fD:
        raise FileExistsError(f'{data_fname} does not exist')

    if not fM:
        raise FileExistsError(f'{mc_fname} does not exist')
    
    data_eff, mc_eff = fD.Get(obj_name), fM.Get(obj_name)
    if not data_eff or not mc_eff:
        print(f"Warning: {obj_name} missing in one of the files")
        return
    
    c = ROOT.TCanvas("c", "c", canvas_size[0], canvas_size[1])
    draw_one_eff(c, data_eff, mc_eff, title, xlabel, ylabel, ylim, ylim_ratio, logx)
    c.Print(output_pdf)

# ----------- scale factors --------------
BASE_DIR = "output/eff"
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
            e = max(eyl, eyh)
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
    leg = ROOT.TLegend(0.23, 0.15, 0.53, 0.26)
    leg.SetNColumns(2)
    leg.SetBorderSize(0)
    leg.AddEntry(graphs[0], labels[0], "lep")

    for g, lab in zip(graphs[1:], labels[1:]):
        leg.AddEntry(g, lab)
    return leg

def make_legend_total(nom, total_band):
    leg = ROOT.TLegend(0.23, 0.25, 0.48, 0.3)
    leg.SetBorderSize(0)
    leg.AddEntry(nom, "Nominal", "lep")
    leg.AddEntry(total_band, "Total syst.", "f")
    return leg

def graph_to_hist_step(g, name, logx=False):
    """Build a TH1D with variable bins from a TGraphAsymmErrors.
       Uses x-exlow and x+exhigh as bin edges; sets bin contents to y."""
    n = g.GetN()
    if n == 0:
        print("G empty")
        return None

    bins = []
    for i in range(n):
        x, y = point(g, i)
        exl, exh, _, _ = errs(g, i)
        left  = x - exl
        right = x + exh

        if right <= left:
            if i == 0 and n > 1:
                x_next, _ = point(g, i+1)
                right = 0.5 * (x + x_next)
                left  = x - (right - x)
            elif i == n-1 and n > 1:
                x_prev, _ = point(g, i-1)
                left  = 0.5 * (x_prev + x)
                right = x + (x - left)
            elif 0 < i < n-1:
                x_prev, _ = point(g, i-1)
                x_next, _ = point(g, i+1)
                left  = 0.5 * (x_prev + x)
                right = 0.5 * (x + x_next)

        if logx:
            if left <= 0:
                left = 1e-12
            if right <= left:
                right = left * (1.0 + 1e-9)

        bins.append((left, right, y))

    edges = [bins[0][0]]
    for _, r, _ in bins:
        edges.append(r)

    for k in range(1, len(edges)):
        if edges[k] <= edges[k-1]:
            edges[k] = edges[k-1] * (1.0 + 1e-9)
        if logx and edges[k] <= 0:
            edges[k] = 1e-12

    from array import array
    h = ROOT.TH1D(name, "", len(edges) - 1, array('d', edges))
    h.SetDirectory(0)
    for i, (_, _, val) in enumerate(bins, start=1):
        h.SetBinContent(i, val)
        h.SetBinError(i, 0.0)
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

FOLDERS  = ["w0", "w1", "w2", "w3", "w4", "w5", "w6"]
LABELS   = ["Nominal", "Tight tag", "Tight #it{A}_{#it{#phi}}<0.01", "Loose #it{A}_{#it{#phi}}<0.03", "ZDC #it{E}<1TeV", "No #it{d}_{0} cut", "#it{p}^{T-P}_{T}<1GeV"]


def plot_scale_factor(*,
        in_fname,
        out_pdf,
        folders = FOLDERS,
        labels = LABELS,
        pT = True,
        sum_unc = False
):

    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetEndErrorSize(0)
    ROOT.gStyle.SetHatchesLineWidth(1)
    ROOT.gStyle.SetHatchesSpacing(1.2)

    ymin, ymax = 0.9, 1.05

    if pT:
        eff_name = 'scale_factor_pT'
        xmin, xmax = 3.0, 50.0
        logx = True

    else:
        eff_name = 'scale_factor_qEta'
        xmin, xmax = -2.4, 2.4
        logx = False
        
    graphs = []
    missing = []
    for w in folders:
        path = os.path.join(BASE_DIR, w, in_fname)
        g = get_graph(path, eff_name)
        if not g: missing.append(path)
        graphs.append(g)

    if graphs[0] is None:
        print("Error: nominal graph missing:", os.path.join(BASE_DIR, folders[0], in_fname))
        if missing:
            print("Also missing:", *missing[1:], sep="\n  ")
        sys.exit(2)
    if any(g is None for g in graphs[1:]):
        print("Warning: missing variations:")
        for i, g in enumerate(graphs):
            if i == 0: continue
            if g is None:
                print(f"  {BASE_DIR}/{folders[i]}/{in_fname}")
                return

    g_nom = graphs[0]

    style_syst(graphs)
    

   

    ROOT.gStyle.SetOptStat(0)
    c = ROOT.TCanvas("c", "c", 850, 720)


    c.SetLogx(logx)
    if pT:
        frame1 = ROOT.TH1F("frame1", ";#it{p}_{T} [GeV];Scale factor", 1, xmin, xmax)
    else:
        frame1 = ROOT.TH1F("frame1", ";#it{q#eta};Scale factor", 1, xmin, xmax)

    if not sum_unc:
        frame1.SetDirectory(0)
        frame1.SetMinimum(ymin); frame1.SetMaximum(ymax)
        frame1.Draw()
        ROOT.gPad.Update()

        h_steps = []
        for idx, g in enumerate(graphs[1:], start=1):
            if not g:
                h_steps.append(None)
                continue
            h = graph_to_hist_step(g, f"h_step_{idx}", logx=logx)
            if h is None:
                print("Histogram is invalid, possible empty graphs")
                return
            style_hist_like_graph(h, g)
            h.Draw("HIST SAME")
            h_steps.append(h)

        g_nom.Draw("P E1 SAME")

        ROOT.gPad.RedrawAxis()
        leg1 = make_legend(graphs, labels)
        leg1.Draw()

        xaxis = frame1.GetXaxis()

        xaxis.SetMoreLogLabels(True)
        xaxis.SetNoExponent(True)
        info_text(pt_variant=pT)

    else:
        syst_graphs = []
        for i in range(1, len(graphs)):
            if graphs[i] is None: continue
            gs = build_syst_graph(g_nom, graphs[i], f"syst_{folders[i]}")
            syst_graphs.append(gs)
        total_band = build_quadrature_band(g_nom, syst_graphs, "syst_total_quad")
        style_total_band(total_band)

        c.Clear(); c.SetLogx(logx)
        frame1.SetDirectory(0)
        frame1.SetMinimum(ymin); frame1.SetMaximum(ymax)
        frame1.Draw()
        total_band.Draw("E2 SAME");
        g_nom.Draw("P E1 SAME")
        leg2 = make_legend_total(g_nom, total_band)
        leg2.Draw()


        xaxis = frame1.GetXaxis()
 
        xaxis.SetMoreLogLabels(True)
        xaxis.SetNoExponent(True)
        info_text(pt_variant=pT)

    c.Modified(); c.Update(); c.Print(out_pdf)


