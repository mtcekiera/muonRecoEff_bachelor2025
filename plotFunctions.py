import ROOT
import sys

### CONFIG ###

RATIO_YMIN, RATIO_YMAX = 0.5, 1.5

#
def add_cut_lines(
    hist,
    x_cuts=None,         # list of x values for vertical cuts
    y_cuts=None,         # list of y values for horizontal cuts
    color=ROOT.kRed,
    style=2,             # 2 = dashed
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

    # vertical cuts: x = const
    for xc in x_cuts:
        line = ROOT.TLine(xc, ymin, xc, ymax)
        line.SetLineColor(color)
        line.SetLineStyle(style)
        line.SetLineWidth(width)
        line.Draw("SAME")
        lines.append(line)

    # horizontal cuts: y = const
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
    x_label="X",
    y_label="Y",
    z_label="",
    title_text="",
    canvas_name="c2d",
    canvas_size=(800, 600),
    logz=False,
    text_ndc_pos=(0.15, 0.93)
):
    c = ROOT.TCanvas(canvas_name, canvas_name, canvas_size[0], canvas_size[1])

    # Bigger margins so axes + colorbar aren't cut
    c.SetLeftMargin(0.13)
    c.SetRightMargin(0.14)   # <- key bit
    c.SetBottomMargin(0.15)
    c.SetTopMargin(0.05)

    if logz:
        c.SetLogz()

    ROOT.gStyle.SetOptStat(0)
    h2.SetStats(0)
    h2.SetTitle("")
    h2.GetXaxis().SetTitle(x_label)
    h2.GetYaxis().SetTitle(y_label)
    if z_label:
        h2.GetZaxis().SetTitle(z_label)

    h2.GetXaxis().SetTitleSize(0.045)
    h2.GetYaxis().SetTitleSize(0.045)
    h2.GetZaxis().SetTitleSize(0.045)

    # h2.GetXaxis().SetTitleOffset(1.2)
    # h2.GetYaxis().SetTitleOffset(0.8)
    # h2.GetZaxis().SetTitleOffset(1.4)  # sometimes needs a bit more

    h2.Draw("COLZ")

    if title_text:
        latex = ROOT.TLatex()
        latex.SetNDC(True)
        latex.SetTextSize(0.04)
        latex.DrawLatex(text_ndc_pos[0], text_ndc_pos[1], title_text)

    c.Update()
    return c

#
def draw_2d_full(
        *,in_fname,
        h2_name,
        x_label = "",
        y_label = "",
        logz = True,
        x_cuts = None,
        y_cuts = None,
        pdf_name
):
    f = ROOT.TFile(in_fname)
    h2 = f.Get(h2_name)
    c = draw_2d_hist(
        h2 = h2,
        x_label=x_label,
        y_label=y_label,
        logz=logz
    )

    lines = add_cut_lines(
        hist = h2,
        x_cuts = x_cuts,
        y_cuts = y_cuts
    )
    c.Print(pdf_name)
    f.Close()


#####
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


def draw_one(canvas, h_data, h_mc, title, logy=False, cut:float|None=None):
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

    # 1) draw first
    h_mc.Draw("HIST")
    h_data.Draw("E1 SAME")

    # 2) now fix min/max
    max_y = max(h_mc.GetMaximum(), h_data.GetMaximum())
    if logy:
        h_mc.SetMinimum(0.1)            # > 0 in log
        h_mc.SetMaximum(max_y * 10.0)   # headroom
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
    leg.AddEntry(h_mc,   "SuperChic #gamma#gamma#rightarrow#mu#mu", "f")
    leg.Draw()

    # 3) force ROOT to recompute the coord system
    pad1.Modified()
    pad1.Update()

    # 4) NOW query pad coords and draw the vertical line
    cut_line = None
    if cut is not None:
        ymin = pad1.GetUymin()
        ymax = pad1.GetUymax()
        # print(f'ymax = {ymax}')
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
        data_file:str,
        mc_file:str,
        output_pdf:str,
        h_name:str,
        cut = None,
        canvas_size=(800, 600),
        logy = False,
        title = '',
        xlabel = '',
        ylabel = '',
):
    f_data = ROOT.TFile.Open(data_file, "READ")
    f_mc   = ROOT.TFile.Open(mc_file,   "READ")
    if not f_data or f_data.IsZombie():
        sys.exit(f"ERROR: cannot open data file: {data_file}")
    if not f_mc or f_mc.IsZombie():
        sys.exit(f"ERROR: cannot open MC file: {mc_file}")

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
    draw_one(c, h_data, h_mc, full_desc, logy=logy, cut=cut)

    c.Print(output_pdf)

    f_data.Close()
    f_mc.Close()
    print(f"Saved: {output_pdf}")