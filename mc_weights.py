import ROOT
import argparse
import numpy as np

def main():


    folders = ["ID_MS", "mu_ID"]
    filenames_part = ["mc_4m7.root", "mc_7m20.root", "mc_20m.root"]
    names = ["4m7", "7m20", "20m"]
    weights = np.array([925, 265, 9.74])
    weights = weights/50000 * 1669.69
    colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen]

    print(weights)

    c = ROOT.TCanvas("c", "Canvas", 800, 600)
    
    c.SetTitle("Tag-probe pair M")

    ROOT.gStyle.SetOptStat(0)

    out_pdf = "./histograms/weights.pdf"
    c.Print(out_pdf+"[")
    for folder in folders:

        hist = []
        legend = ROOT.TLegend(0.7, 0.7, 0.9, 0.9)



        f_all = ROOT.TFile.Open(f"./output/{folder}/mc_histograms.root")
        hist_all = f_all.Get("TPpair_M_postsel")
        
        hist_all.SetLineColor(ROOT.kBlack)
        hist_all.SetFillColorAlpha(ROOT.kGray, 0.5)
        
        hist_all.Draw("HIST")
        legend.AddEntry(hist_all, "combined", "F")


        for i in range(3):
            hist.append(ROOT.TH1F(names[i], "", 100, 0, 100))

            f = ROOT.TFile.Open(f"./output/{folder}/{filenames_part[i]}")
            if not f or f.IsZombie():
                print(f"Error opening file {filenames_part[i]}")
                continue

            t = f.Get("G2TauTree_output")
            if not t:
                print(f"Tree not found in file {filenames_part[i]}")
                f.Close()
                continue

            for event in t:
                for value in event.TPpair_M_postsel:
                    hist[i].Fill(value)
            
            hist[i].Scale(weights[i])

            hist[i].SetLineColor(colors[i])
            hist[i].SetFillColor(colors[i])
            hist[i].SetFillStyle(3004)

            hist[i].Draw("HIST SAME")

            legend.AddEntry(hist[i], names[i], "F")

            f.Close()

        legend.Draw()

        hist_all.SetTitle("Tag-probe pair Total M "+folder)
        hist_all.GetXaxis().SetTitle("Tag-probe pair Total M (GeV)")
        hist_all.GetYaxis().SetTitle("Events")
        
        
        c.Print(out_pdf)

        f_all.Close()
    c.Print(out_pdf+"]")


if __name__ == "__main__":
    main()
