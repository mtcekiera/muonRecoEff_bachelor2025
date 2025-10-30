import ROOT
import argparse
import numpy as np

def main():


    folders = ["ID_MS", "mu_ID"]
    # File details
    filenames_part = ["mc_4m7.root", "mc_7m20.root", "mc_20m.root"]
    names = ["4m7", "7m20", "20m"]
    weights = np.array([925, 265, 9.74])
    weights = weights/50000 * 1669.69
    colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen]  # Colors for each histogram

    print(weights)

    # Create canvas
    c = ROOT.TCanvas("c", "Canvas", 800, 600)
    
    # Set the title for the canvas
    c.SetTitle("Tag-probe pair M")

    # Disable the statistics box
    ROOT.gStyle.SetOptStat(0)

    out_pdf = "./histograms/weights.pdf"
    c.Print(out_pdf+"[")
    for folder in folders:

        # Initialize histograms list
        hist = []

        # Create legend
        legend = ROOT.TLegend(0.7, 0.7, 0.9, 0.9)  # Legend position (x1, y1, x2, y2)



        # Load the combined histogram (hist_all)
        f_all = ROOT.TFile.Open(f"./output/{folder}/mc_histograms.root")
        hist_all = f_all.Get("TPpair_M_postsel")
        
        # Style for the combined histogram
        hist_all.SetLineColor(ROOT.kBlack)  # Set black line color for hist_all
        hist_all.SetFillColorAlpha(ROOT.kGray, 0.5)  # Set a semi-transparent fill color for hist_all
        
        hist_all.Draw("HIST")  # Draw hist_all first
        legend.AddEntry(hist_all, "combined", "F")  # "F" means filled


        # Loop over the files and process each histogram
        for i in range(3):
            # Initialize histogram
            hist.append(ROOT.TH1F(names[i], "", 100, 0, 100))  # Number of bins set to 100 for example

            # Open ROOT file
            f = ROOT.TFile.Open(f"./output/{folder}/{filenames_part[i]}")
            if not f or f.IsZombie():
                print(f"Error opening file {filenames_part[i]}")
                continue

            # Get the tree
            t = f.Get("G2TauTree_output")
            if not t:
                print(f"Tree not found in file {filenames_part[i]}")
                f.Close()
                continue

            # Fill the histogram with data from the tree
            for event in t:
                for value in event.TPpair_M_postsel:
                    hist[i].Fill(value)
            
            # Scale the histogram with the weight
            hist[i].Scale(weights[i])

            # Set histogram color
            hist[i].SetLineColor(colors[i])  # Set line color
            hist[i].SetFillColor(colors[i])  # Set fill color
            hist[i].SetFillStyle(3004)  # Set transparency for filled histograms

            # Draw the histogram on the canvas (on top of hist_all)
            hist[i].Draw("HIST SAME")  # Draw the first histogram, others on top of the previous

            # Add the histogram to the legend
            legend.AddEntry(hist[i], names[i], "F")  # "F" means filled

            # Close the ROOT file after processing
            f.Close()

        # Draw the legend
        legend.Draw()

        # Set the y-axis to log scale
        # c.SetLogy()

        # Set axis labels
        hist_all.SetTitle("Tag-probe pair Total M "+folder)
        hist_all.GetXaxis().SetTitle("Tag-probe pair Total M (GeV)")
        hist_all.GetYaxis().SetTitle("Events")
        
        
        # Save the canvas to a PDF file
        # c.SaveAs(f"./histograms/weights.pdf")
        c.Print(out_pdf)

        # Close the file for hist_all
        f_all.Close()
    c.Print(out_pdf+"]")


if __name__ == "__main__":
    main()
