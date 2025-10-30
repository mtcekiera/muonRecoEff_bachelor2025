#!/usr/bin/env python3
import sys
import argparse
import ROOT

ROOT.gROOT.SetBatch(True)

# ---------------------------- USER-CONFIGURABLE BLOCK -------------------------
# Edit this list to select which histograms to plot.
# Each entry:
#   name   : histogram path/name in BOTH files
#   title  : full title "Main title;X axis;Y axis"
#   logy   : True/False for log scale on the top pad
#   rebin  : optional integer rebin factor (default 1)
#   scale_mc_to_data : optional bool to area-scale MC to match Data (default False)
HISTOS = [
    {"name": "h_mass",    "title": "Invariant mass;M [GeV];Events", "logy": False},
    {"name": "h_pt",      "title": "p_{T};p_{T} [GeV];Events",      "logy": True, "rebin": 2},
    {"name": "h_eta",     "title": "Pseudo-rapidity;#eta;Events",   "logy": False},
]
# Default y-range for the ratio plot (you can change globally here)
RATIO_YMIN, RATIO_YMAX = 0.5, 1.5
# -------------------------- END USER-CONFIGURABLE BLOCK -----------------------


def get_hist(tfile, name):
    h = tfile.Get(name)
    if not h:
        return None
    # Work with an owned clone so we can style/rebin without touching the file object
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

    ratio.SetTitle("")
    ratio.GetYaxis().SetTitle("Data / MC")
    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetYaxis().SetTitleSize(0.11)
    ratio.GetYaxis().SetTitleOffset(0.45)
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

    # Upper pad
    pad1.cd()
    if logy:
        pad1.SetLogy()

    # Adjust y-range for nicer visuals on log/lin
    # Compute maxima after drawing styles
    style_mc_hist(mc_h)
    style_data_hist(data_h)

    # Ensure the axes titles are set from the supplied 'title'
    if title:
        data_h.SetTitle(title)
    # Establish draw order: MC first (as filled HIST), then Data with error bars
    drawopt_mc = "HIST"
    mc_h.Draw(drawopt_mc)
    data_h.Draw("E1 SAME")

    # y-range
    max_y = max(mc_h.GetMaximum(), data_h.GetMaximum())
    if logy:
        mc_h.SetMinimum(max(1e-3, 0.5e-3))  # small positive min
        mc_h.SetMaximum(max_y * 10.0)
    else:
        mc_h.SetMinimum(0.0)
        mc_h.SetMaximum(max_y * 1.35)

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
    frame.GetYaxis().SetTitle("Data / MC")
    frame.GetYaxis().SetNdivisions(505)
    frame.GetYaxis().SetTitleSize(0.11)
    frame.GetYaxis().SetTitleOffset(0.45)
    frame.GetYaxis().SetLabelSize(0.10)
    frame.GetXaxis().SetTitle(data_h.GetXaxis().GetTitle())
    frame.GetXaxis().SetTitleSize(0.12)
    frame.GetXaxis().SetLabelSize(0.10)

    band.Draw("E2 SAME")
    ratio.Draw("E1 SAME")

    # Draw horizontal line at 1
    line = ROOT.TLine(data_h.GetXaxis().GetXmin(), 1.0,
                      data_h.GetXaxis().GetXmax(), 1.0)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kGray + 2)
    line.Draw("SAME")

    canvas.Update()


def main():
    parser = argparse.ArgumentParser(description="Plot Data vs MC histograms with ratio (one per PDF page).")
    parser.add_argument("data_file", help="ROOT file with Data histograms")
    parser.add_argument("mc_file",   help="ROOT file with MC histograms")
    parser.add_argument("output_pdf", help="Output PDF file name")
    args = parser.parse_args()

    f_data = ROOT.TFile.Open(args.data_file, "READ")
    f_mc   = ROOT.TFile.Open(args.mc_file,   "READ")
    if not f_data or f_data.IsZombie():
        sys.exit(f"ERROR: cannot open data file: {args.data_file}")
    if not f_mc or f_mc.IsZombie():
        sys.exit(f"ERROR: cannot open MC file: {args.mc_file}")

    c = ROOT.TCanvas("c", "c", 900, 900)
    c.Print(args.output_pdf + "[")

    for cfg in HISTOS:
        name   = cfg["name"]
        title  = cfg.get("title", "")
        logy   = bool(cfg.get("logy", False))
        rebin  = int(cfg.get("rebin", 1))
        scale_mc_to_data = bool(cfg.get("scale_mc_to_data", False))

        h_data = get_hist(f_data, name)
        h_mc   = get_hist(f_mc,   name)

        if h_data is None:
            print(f"[WARN] Data histogram '{name}' not found, skipping.")
            continue
        if h_mc is None:
            print(f"[WARN] MC histogram '{name}' not found, skipping.")
            continue

        # Check binning compatibility
        same_binning = (
            h_data.GetNbinsX() == h_mc.GetNbinsX() and
            abs(h_data.GetXaxis().GetXmin() - h_mc.GetXaxis().GetXmin()) < 1e-9 and
            abs(h_data.GetXaxis().GetXmax() - h_mc.GetXaxis().GetXmax()) < 1e-9
        )
        if not same_binning:
            print(f"[WARN] Histogram '{name}' has different binning in Data and MC. Skipping.")
            continue

        if rebin and rebin > 1:
            h_data.Rebin(rebin)
            h_mc.Rebin(rebin)

        if scale_mc_to_data:
            int_data = h_data.Integral()
            int_mc   = h_mc.Integral()
            if int_mc > 0:
                h_mc.Scale(int_data / int_mc)

        h_data.SetTitle(title)  # also sets axes if provided as "title;X;Y"
        draw_one(c, h_data, h_mc, title, logy=logy)
        c.Print(args.output_pdf)

    c.Print(args.output_pdf + "]")
    f_data.Close()
    f_mc.Close()
    print(f"Saved: {args.output_pdf}")


if __name__ == "__main__":
    main()
