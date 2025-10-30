#!/usr/bin/env python3
import ROOT

def plot(data_file, mc_file, out_pdf, title_data="Data", title_mc="MC", logy=False):
    """
    Draws histograms from data_file and mc_file (same structure)
    overlayed on one canvas per histogram, and writes all pages into a multi-page PDF.
    """

    # Style setup
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning

    f_data = ROOT.TFile.Open(data_file)
    f_mc   = ROOT.TFile.Open(mc_file)
    if not f_data or f_data.IsZombie(): raise RuntimeError(f"Cannot open {data_file}")
    if not f_mc   or f_mc.IsZombie():   raise RuntimeError(f"Cannot open {mc_file}")

    # Collect hist names (common to both files)
    data_keys = [k.GetName() for k in f_data.GetListOfKeys() if k.GetClassName().startswith("TH")]
    mc_keys   = [k.GetName() for k in f_mc.GetListOfKeys()   if k.GetClassName().startswith("TH")]
    common = sorted(set(data_keys) & set(mc_keys))
    if not common:
        print("No matching histograms found.")
        return

    print(f"[i] Found {len(common)} histograms to compare.")

    c = ROOT.TCanvas("c", "c", 800, 700)
    c.Print(out_pdf + "[")   # open multi-page PDF

    for name in common:
        h_data = f_data.Get(name)
        h_mc   = f_mc.Get(name)
        if not h_data or not h_mc:
            continue

        # Check histogram types
        print(f"Data histogram {name} is of type {type(h_data)}")
        print(f"MC histogram {name} is of type {type(h_mc)}")

        # Handle TH1I histograms (integer-based)
        # Convert TH1I to TH1D for better handling (e.g., for scaling and normalization)
        if isinstance(h_data, ROOT.TH1I):
            h_data = h_data.Clone(h_data.GetName() + "_float")
            h_data.SetStats(0)
            for bin in range(1, h_data.GetNbinsX() + 1):
                h_data.SetBinContent(bin, float(h_data.GetBinContent(bin)))

        if isinstance(h_mc, ROOT.TH1I):
            h_mc = h_mc.Clone(h_mc.GetName() + "_float")
            h_mc.SetStats(0)
            for bin in range(1, h_mc.GetNbinsX() + 1):
                h_mc.SetBinContent(bin, float(h_mc.GetBinContent(bin)))

        # Styling
        h_data.SetMarkerStyle(20)
        h_data.SetMarkerColor(ROOT.kBlack)
        h_data.SetLineColor(ROOT.kBlack)
        h_data.SetTitle(name)

        h_mc.SetLineColor(ROOT.kRed+1)
        h_mc.SetFillColorAlpha(ROOT.kRed, 0.25)
        h_mc.SetLineWidth(2)

        # Determine Y range
        max_y = 1.2 * max(h_data.GetMaximum(), h_mc.GetMaximum())
        h_mc.SetMaximum(max_y)
        h_mc.SetMinimum(0 if not logy else 1e-3)

        # Draw order: MC first (filled), then data points
        c.Clear()
        if logy: c.SetLogy(True)
        else:    c.SetLogy(False)
        h_mc.Draw("HIST")
        h_data.Draw("E SAME")

        # Legend
        leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(h_data, title_data, "lep")
        leg.AddEntry(h_mc, title_mc, "f")
        leg.Draw()

        c.Print(out_pdf)  # append page


    c.Print(out_pdf + "]")   # close PDF
    print(f"[✓] Saved comparison PDF: {out_pdf}")

    f_data.Close()
    f_mc.Close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compare histograms from two ROOT files and save to multi-page PDF.")
    parser.add_argument("data_file", help="Input ROOT file with data histograms")
    parser.add_argument("mc_file", help="Input ROOT file with MC histograms")
    parser.add_argument("out_pdf", help="Output multi-page PDF file")
    parser.add_argument("--title-data", default="Data", help="Legend title for data histograms")
    parser.add_argument("--title-mc", default="MC", help="Legend title for MC histograms")
    parser.add_argument("--logy", action="store_true", help="Use logarithmic scale for Y axis")
    args = parser.parse_args()

    plot(args.data_file, args.mc_file, args.out_pdf, args.title_data, args.title_mc, args.logy)
