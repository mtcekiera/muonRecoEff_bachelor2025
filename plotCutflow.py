import ROOT

def plot_cutflow(data_file_1, data_file_2, out_pdf, title_data_1="Data 1", title_data_2="Data 2", logy=False):
    """
    Draws 'hist_eps_cutflow' from data_file_1 and data_file_2 on separate pages of a multi-page PDF.
    """
    # Style setup
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning

    # Open the ROOT files
    f_data_1 = ROOT.TFile.Open(data_file_1)
    f_data_2 = ROOT.TFile.Open(data_file_2)
    
    if not f_data_1 or f_data_1.IsZombie(): 
        raise RuntimeError(f"Cannot open {data_file_1}")
    if not f_data_2 or f_data_2.IsZombie():   
        raise RuntimeError(f"Cannot open {data_file_2}")

    # Retrieve 'hist_eps_cutflow' histograms
    h_data_1 = f_data_1.Get("hist_eps_cutflow")
    h_data_2 = f_data_2.Get("hist_eps_cutflow")

    if not h_data_1 or not h_data_2:
        print("Error: 'hist_eps_cutflow' not found in one or both files.")
        return

    print(f"[i] Found 'hist_eps_cutflow' in both files.")

    # Check that the histograms are of type TH1I (integer)
    if not isinstance(h_data_1, ROOT.TH1I) or not isinstance(h_data_2, ROOT.TH1I):
        print("Warning: The histograms are not of type TH1I. Please check the type of the histograms.")
        return

    # Open multi-page PDF
    c = ROOT.TCanvas("c", "c", 800, 700)
    c.Print(out_pdf + "[")  # Open multi-page PDF

    # Plot the first dataset (data_file_1)
    h_data_1.SetMarkerStyle(20)
    h_data_1.SetMarkerColor(ROOT.kBlack)
    h_data_1.SetLineColor(ROOT.kBlack)
    h_data_1.SetTitle("hist_eps_cutflow from Data 1")
    
    h_data_2.SetLineColor(ROOT.kRed + 1)
    h_data_2.SetFillColorAlpha(ROOT.kRed, 0.25)
    h_data_2.SetLineWidth(2)

    # Check if the histograms are being filled properly
    print(f"[i] Data 1 histogram entries: {h_data_1.GetEntries()}")
    print(f"[i] Data 2 histogram entries: {h_data_2.GetEntries()}")

    # Ensure the bins have non-zero entries
    for i in range(1, h_data_1.GetNbinsX() + 1):
        print(f"Data 1 bin {i}: {h_data_1.GetBinContent(i)}")
    for i in range(1, h_data_2.GetNbinsX() + 1):
        print(f"Data 2 bin {i}: {h_data_2.GetBinContent(i)}")

    # Determine Y range
    max_y = 1.2 * max(h_data_1.GetMaximum(), h_data_2.GetMaximum())
    h_data_1.SetMaximum(max_y)
    h_data_1.SetMinimum(0 if not logy else 1e-3)

    # Set log scale if requested
    if logy:
        c.SetLogy(True)
    else:
        c.SetLogy(False)
    
    # Clear the canvas and plot data 1
    c.Clear()
    h_data_1.Draw("E")
    
    # Add the legend
    leg = ROOT.TLegend(0.65, 0.75, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h_data_1, title_data_1, "lep")
    leg.Draw()

    # Save the first plot to the PDF
    c.Print(out_pdf)  # Append page

    # Plot the second dataset (data_file_2)
    h_data_2.SetMarkerStyle(20)
    h_data_2.SetMarkerColor(ROOT.kBlack)
    h_data_2.SetLineColor(ROOT.kBlack)
    h_data_2.SetTitle("hist_eps_cutflow from Data 2")
    
    # Ensure bins are non-zero
    for i in range(1, h_data_2.GetNbinsX() + 1):
        print(f"Data 2 bin {i}: {h_data_2.GetBinContent(i)}")
    
    # Normalize to unity (optional, comment out if not desired)
    if h_data_2.Integral() > 0: h_data_2.Scale(1.0 / h_data_2.Integral())

    # Determine Y range
    max_y = 1.2 * h_data_2.GetMaximum()
    h_data_2.SetMaximum(max_y)
    h_data_2.SetMinimum(0 if not logy else 1e-3)

    # Set log scale if requested
    if logy:
        c.SetLogy(True)
    else:
        c.SetLogy(False)
    
    # Clear the canvas and plot data 2
    c.Clear()
    h_data_2.Draw("E")
    
    # Add the legend
    leg.Clear()
    leg.AddEntry(h_data_2, title_data_2, "lep")
    leg.Draw()

    # Save the second plot to the PDF
    c.Print(out_pdf)  # Append page

    c.Print(out_pdf + "]")  # Close PDF
    print(f"[✓] Saved comparison PDF: {out_pdf}")

    # Close ROOT files
    f_data_1.Close()
    f_data_2.Close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Plot 'hist_eps_cutflow' histograms from two data ROOT files and save to multi-page PDF.")
    parser.add_argument("data_file_1", help="Input ROOT file with data histograms (data set 1)")
    parser.add_argument("data_file_2", help="Input ROOT file with data histograms (data set 2)")
    parser.add_argument("out_pdf", help="Output multi-page PDF file")
    parser.add_argument("--title-data-1", default="Data 1", help="Legend title for the first data set")
    parser.add_argument("--title-data-2", default="Data 2", help="Legend title for the second data set")
    parser.add_argument("--logy", action="store_true", help="Use logarithmic scale for Y axis")
    args = parser.parse_args()

    plot_cutflow(args.data_file_1, args.data_file_2, args.out_pdf, args.title_data_1, args.title_data_2, args.logy)
