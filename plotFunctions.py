import ROOT
import sys

### CONFIG ###

RATIO_YMIN, RATIO_YMAX = 0.5, 1.5

#
def add_cut_lines_2d(
    h2,
    x_cuts=None,         # list of x values for vertical cuts
    y_cuts=None,         # list of y values for horizontal cuts
    color=ROOT.kRed,
    style=2,             # 2 = dashed
    width=2
):
    """
    Draw red dashed cut lines on a 2D histogram (already drawn).

    Returns a list of TLine objects so they don't get garbage-collected.
    """
    if x_cuts is None:
        x_cuts = []
    if y_cuts is None:
        y_cuts = []

    xmin = h2.GetXaxis().GetXmin()
    xmax = h2.GetXaxis().GetXmax()
    ymin = h2.GetYaxis().GetXmin()
    ymax = h2.GetYaxis().GetXmax()

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

    lines = add_cut_lines_2d(
        h2 = h2,
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
    # Work with an owned clone so we can style without touching the file object
    h = h.Clone(name + "_clone")
    h.SetDirectory(0)
    # Ensure proper error handling
    if not h.GetSumw2N():
        h.Sumw2()
    return h


def style_data_hist(h):
    h.SetMarkerStyle(20)
    h.SetMarkerSize(0.9)
    h.SetMarkerColor(ROOT.kBlack)
    h.SetLineColor(ROOT.kBlack)
    h.SetLineWidth(2)


def style_mc_hist(h):
    # nice blue line + light fill
    h.SetLineColor(ROOT.kAzure + 2)
    h.SetLineWidth(2)
    h.SetFillColorAlpha(ROOT.kAzure + 1, 0.35)


def make_ratio(data, mc):
    """Return (ratio_hist, mc_uncertainty_band TGraphErrors). Ratio = Data/MC."""
    ratio = data.Clone(data.GetName() + "_ratio")
    nb = ratio.GetNbinsX()

    # Build MC relative uncertainty band (1 ± sigma_MC/MC)
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
            # Propagate errors assuming uncorrelated:
            if D > 0.0:
                rel = (eD / D) ** 2 + (eM / M) ** 2
                er  = r * (rel ** 0.5)
            else:
                er = 0.0
        else:
            # No MC in the bin -> define as 0 with 0 error (you can choose to mask instead)
            r, er = 0.0, 0.0

        ratio.SetBinContent(i, r)
        ratio.SetBinError(i, er)

        # Uncertainty band for MC: centered at 1, with ey = eM/M when M>0 else 0
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

    # ratio.SetTitle("")
    # ratio.GetYaxis().SetTitle("Data / MC")
    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetYaxis().SetTitleSize(0.11)
    # ratio.GetYaxis().SetTitleOffset(0.45)
    ratio.GetYaxis().SetLabelSize(0.10)
    ratio.GetXaxis().SetLabelSize(0.10)
    ratio.GetXaxis().SetTitleSize(0.12)
    ratio.GetXaxis().SetTitleOffset(1.0)
    ratio.SetMarkerStyle(20)
    ratio.SetMarkerSize(0.8)
    ratio.SetLineColor(ROOT.kBlack)
    ratio.SetMarkerColor(ROOT.kBlack)

    return ratio, band


def draw_one(canvas, data_h, mc_h, title, logy=False):
    # Create two pads: upper for spectra, lower for ratio
    canvas.Clear()
    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.30, 1, 1.00)
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.00, 1, 0.30)
    pad1.SetBottomMargin(0.02)
    pad2.SetTopMargin(0.03)
    pad2.SetBottomMargin(0.35)
    pad1.Draw()
    pad2.Draw()
    pad2.SetGrid(True)

    # Upper pad
    pad1.cd()
    if logy:
        pad1.SetLogy()

    # Adjust y-range for nicer visuals on log/lin
    # Compute maxima after drawing styles
    style_mc_hist(mc_h)
    style_data_hist(data_h)

    # Ensure the axes titles are set from the supplied 'title'
    # if title:
    data_h.SetTitle(title)
    mc_h.Draw("HIST")
    data_h.Draw("E1 SAME")
    mc_h.GetXaxis().SetLabelSize(0)

    # y-range
    max_y = max(mc_h.GetMaximum(), data_h.GetMaximum())
    if logy:
        mc_h.SetMinimum(max(1e-3, 0.5e-3))  # small positive min
        mc_h.SetMaximum(max_y * 10.0)
    else:
        mc_h.SetMinimum(0.0)
        mc_h.SetMaximum(max_y * 1.35)

    # Delete stats
    ROOT.gStyle.SetOptStat(0)

    # Legend
    leg = ROOT.TLegend(0.60, 0.72, 0.88, 0.89)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(data_h, "Data", "lep")
    leg.AddEntry(mc_h,   "MC",   "f")
    leg.Draw()

    # Lower pad (ratio)
    pad2.cd()
    ratio, band = make_ratio(data_h, mc_h)
    ratio.GetYaxis().SetRangeUser(RATIO_YMIN, RATIO_YMAX)

    # Draw band first, then ratio points
    frame = pad2.DrawFrame(
        data_h.GetXaxis().GetXmin(), RATIO_YMIN,
        data_h.GetXaxis().GetXmax(), RATIO_YMAX
    )
    # frame.GetYaxis().SetTitle(data_h.GetYaxis().GetTitle())
    frame.GetYaxis().SetNdivisions(505)
    frame.GetYaxis().SetTitleSize(0.11)
    frame.GetYaxis().SetTitleOffset(0.45)
    frame.GetYaxis().SetLabelSize(0.10)
    frame.GetXaxis().SetTitle(data_h.GetXaxis().GetTitle())
    frame.GetXaxis().SetTitleSize(0.12)
    frame.GetXaxis().SetLabelSize(0.10)
    # data_h.GetYaxis().SetTitle(data_h.GetYaxis().GetTitle())

    band.Draw("E2 SAME")
    ratio.Draw("E1 SAME")

    # Draw horizontal line at 1
    line = ROOT.TLine(data_h.GetXaxis().GetXmin(), 1.0,
                      data_h.GetXaxis().GetXmax(), 1.0)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kRed)
    line.Draw("SAME")

    canvas.Update()


def plot_1d_histogram(
        *,
        data_file:str,
        mc_file:str,
        output_pdf:str,
        h_name:str,
        canvas_size=(800, 600),
        logy = False,
        title = '',
        xlabel = '',
        ylabel = ''
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
    h_data.SetTitle(title)  # also sets axes if provided as "title;X;Y"
    draw_one(c, h_data, h_mc, full_desc, logy=logy)
    c.Print(output_pdf)

    f_data.Close()
    f_mc.Close()
    print(f"Saved: {output_pdf}")