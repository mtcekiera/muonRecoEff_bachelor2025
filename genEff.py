import ROOT
import os, sys
from array import array

# GLOBAL
BIN_EDGES = [3.0, 3.5, 4.0, 4.5, 5.5, 7.5, 10.0, 12.5, 15.0, 50.0]
HNAME_PASS_PT  = "eps_pass"
HNAME_TOTAL_PT = "eps_total"
HNAME_PASS_QETA  = "eps_qEta_pass"
HNAME_TOTAL_QETA = "eps_qEta_total"


def _find_hist_recursive(d, name):
    h = d.Get(name)
    if h: return h
    for key in d.GetListOfKeys():
        obj = d.Get(key.GetName())
        if isinstance(obj, ROOT.TDirectory):
            h2 = _find_hist_recursive(obj, name)
            if h2: return h2
    return None

def debug_consistency(h_pass, h_total):
    n = h_pass.GetNbinsX()
    for i in range(0, n + 2):  # 0 = underflow, n+1 = overflow
        p = h_pass.GetBinContent(i)
        t = h_total.GetBinContent(i)
        if p > t or t < 0 or p < 0:
            print(f"BAD BIN i={i}: pass={p}, total={t}")

    print("Done checking bins")

def _rebin_to(h, edges):
    nb = len(edges) - 1
    return h.Rebin(nb, h.GetName() + "__rebin", array('d', edges))

def get_2d_efficiency(path, hname_pass, hname_total):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None

    h2_pass  = _find_hist_recursive(f, hname_pass)
    h2_total = _find_hist_recursive(f, hname_total)
    if not h2_pass or not h2_total:
        f.Close()
        return None
    h2_pass.Sumw2();
    h2_total.Sumw2();

    h2_ratio = h2_pass.Clone("h2_ratio")
    h2_ratio.SetDirectory(0)

    h2_ratio.SetTitle("ratio;p_{T};q#eta")
    h2_ratio.Divide(h2_total)

    f.Close()

    return h2_ratio 

def combine_2d_total_eff(eff1, eff2):
    if not eff1 or not eff2:
        print('Efficency histograms empty!')
        return None
    eff1.Sumw2();
    eff2.Sumw2();
    eff_total = eff1.Clone("eps_2d")
    eff_total.SetTitle('eps_2d;p_{T},q#eta')
    eff_total.Multiply(eff2)
    return eff_total



def get_efficiency(path, hname_pass, hname_total, rebin=False, edges=None):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None

    h_pass  = _find_hist_recursive(f, hname_pass)
    h_total = _find_hist_recursive(f, hname_total)
    if not h_pass or not h_total:
        f.Close()
        return None

    if rebin and edges:
        h_pass  = _rebin_to(h_pass,  edges)
        h_total = _rebin_to(h_total, edges)

    # print("nbinsX:", h_pass.GetNbinsX(), h_total.GetNbinsX())
    # print("Entries:", h_pass.GetEntries(), h_total.GetEntries())

    debug_consistency(h_pass, h_total)
    if not ROOT.TEfficiency.CheckConsistency(h_pass, h_total):
        print(f"Warning: inconsistent pass/total in {path}")
        f.Close()
        return None

    te = ROOT.TEfficiency(h_pass, h_total)
    te.SetStatisticOption(ROOT.TEfficiency.kFNormal)

    f.Close()
    return te


def combine_total_eff(eff1, eff2):
    if eff1 is None or eff2 is None: return None
    n = eff1.GetTotalHistogram().GetNbinsX()
    gr = ROOT.TGraphAsymmErrors(n)
    for i in range(1, n+1):
        e1 = eff1.GetEfficiency(i);  e2 = eff2.GetEfficiency(i)
        u1 = eff1.GetEfficiencyErrorUp(i);  d1 = eff1.GetEfficiencyErrorLow(i)
        u2 = eff2.GetEfficiencyErrorUp(i);  d2 = eff2.GetEfficiencyErrorLow(i)
        val = e1 * e2
        eup = val * ((u1/e1 if e1>0 else 0.)**2 + (u2/e2 if e2>0 else 0.)**2)**0.5
        edn = val * ((d1/e1 if e1>0 else 0.)**2 + (d2/e2 if e2>0 else 0.)**2)**0.5
        x  = eff1.GetTotalHistogram().GetBinCenter(i)
        ex = eff1.GetTotalHistogram().GetBinWidth(i)/2.0
        gr.SetPoint(i-1, x, val)
        gr.SetPointError(i-1, ex, ex, edn, eup)
    return gr



def main():
    if(len(sys.argv)!=4):
        print("Usage: python genEff.py wi/input_file output_file make_2d")
        return
    
    wp_in_fname = sys.argv[1]
    out_fname = sys.argv[2]
    make_2d = not int(sys.argv[3])

    print(f'MAKE 2D = {make_2d}')

    id_path = os.path.join("output/ID_MS", wp_in_fname)
    mu_path = os.path.join("output/mu_ID", wp_in_fname)

    print(f"{wp_in_fname}->{out_fname}")
    print(f"Opening {id_path}")
    id_eff_pt = get_efficiency(id_path, HNAME_PASS_PT, HNAME_TOTAL_PT, True, BIN_EDGES)
    id_eff_qeta = get_efficiency(id_path, HNAME_PASS_QETA, HNAME_TOTAL_QETA, False)
    if not id_eff_pt or not id_eff_qeta:
        print("ID_MS pt efficiency error")
        return
    
    print(f"Opening {mu_path}")
    mu_eff_pt = get_efficiency(mu_path, HNAME_PASS_PT, HNAME_TOTAL_PT, True, BIN_EDGES)
    mu_eff_qeta = get_efficiency(mu_path, HNAME_PASS_QETA, HNAME_TOTAL_QETA, False)
    if not mu_eff_pt or not mu_eff_qeta:
        print("mu_ID efficiency error")
        return
    
    print("Calculating total eff")
    total_eff = combine_total_eff(id_eff_pt, mu_eff_pt)
    total_eff_qeta = combine_total_eff(id_eff_qeta, mu_eff_qeta)
    if not total_eff or not total_eff_qeta:
        print("Total efficiency error")
        return


    print(f"Saving to {out_fname}")
    f_out = ROOT.TFile(out_fname, "RECREATE")
    id_eff_pt.SetName("ID_MS_eff")
    mu_eff_pt.SetName("mu_ID_eff")
    total_eff.SetName("total_eff")
    id_eff_pt.Write()
    mu_eff_pt.Write()
    total_eff.Write()

    id_eff_qeta.SetName("ID_MS_qeta_eff")
    mu_eff_qeta.SetName("mu_ID_qeta_eff")
    total_eff_qeta.SetName("total_qeta_eff")
    id_eff_qeta.Write()
    mu_eff_qeta.Write()
    total_eff_qeta.Write()
    # total_eff.Write()


    if make_2d:
        print("Making 2d efficiency plots")
        id_2d_eff = get_2d_efficiency(id_path, 'eps_2d_pass', 'eps_2d_total')
        mu_2d_eff = get_2d_efficiency(mu_path, 'eps_2d_pass', 'eps_2d_total')
        total_2d_eff = combine_2d_total_eff(id_2d_eff, mu_2d_eff)

        id_2d_eff.SetName("ID_MS_2d_eff")
        mu_2d_eff.SetName("mu_ID_2d_eff")
        total_2d_eff.SetName("total_2d_eff")


        f_out.cd()
        id_2d_eff.Write()
        mu_2d_eff.Write()
        total_2d_eff.Write()


    f_out.Close()

if __name__ == "__main__":
    main()