import ROOT
import sys
from array import array
import math

def _get_point(g, i):
    x = array('d', [0.0]); y = array('d', [0.0])
    g.GetPoint(i, x, y)
    return (x[0], y[0],
            g.GetErrorXlow(i),  g.GetErrorXhigh(i),
            g.GetErrorYlow(i),  g.GetErrorYhigh(i))

def _rel_close(a, b, tol):
    # absolute-or-relative tolerance
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))

def ratio_of_TGraphs(g1, g2, name):
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
    g.SetName(name)
    return g

def ratio_TGraphAsymmErrors(g_num, g_den, name="ratio", title="ratio", xmatch_tol=1e-9, conservative_fallback=True):
    """
    Build r = g_num / g_den with asymmetric errors:
      up:   σ_up = r * sqrt( (σ_num^+/num)^2 + (σ_den^-/den)^2 )
      down: σ_dn = r * sqrt( (σ_num^-/num)^2 + (σ_den^+/den)^2 )
    Near zeros or invalid denominators, optionally fall back to a conservative envelope.
    Points are paired by matching x within xmatch_tol.
    """
    out = ROOT.TGraphAsymmErrors(); ROOT.SetOwnership(out, False)
    out.SetName(name); out.SetTitle(title)

    # index denominator by x for quick lookup
    den_points = []
    for j in range(g_den.GetN()):
        den_points.append(_get_point(g_den, j))

    for i in range(g_num.GetN()):
        x1, y1, exl1, exh1, eyl1, eyh1 = _get_point(g_num, i)

        # find a denominator point with the same x (within tolerance)
        jmatch = None
        for j, (x2, _, _, _, _, _) in enumerate(den_points):
            if _rel_close(x1, x2, xmatch_tol):
                jmatch = j
                break
        if jmatch is None:
            continue

        x2, y2, exl2, exh2, eyl2, eyh2 = den_points[jmatch]
        if y2 <= 0:
            continue  # undefined ratio

        r = y1 / y2

        # default: asymmetric uncertainty propagation (uncorrelated)
        valid_prop = (y1 > 0) and (y2 > 0)
        if valid_prop:
            up  = r * math.hypot( (eyh1 / y1) if y1 > 0 else 0.0,
                                  (eyl2 / y2) if y2 > 0 else 0.0 )
            dn  = r * math.hypot( (eyl1 / y1) if y1 > 0 else 0.0,
                                  (eyh2 / y2) if y2 > 0 else 0.0 )
        else:
            up = dn = 0.0

        # fallback to conservative envelope when propagation is ill-defined or requested
        if conservative_fallback and (not valid_prop or not math.isfinite(up) or not math.isfinite(dn)):
            # clamp to physical domain and avoid division singularities
            num_hi = y1 + eyh1
            num_lo = max(y1 - eyl1, 0.0)
            den_hi = y2 + eyh2
            den_lo = max(y2 - eyl2, 1e-12)
            r_hi = num_hi / den_lo - r
            r_lo = r - (num_lo / den_hi if den_hi > 0 else r)
            up = max(0.0, r_hi)
            dn = max(0.0, r_lo)

        # x errors: take the larger on each side
        exl = max(exl1, exl2)
        exh = max(exh1, exh2)

        p = out.GetN()
        out.SetPoint(p, x1, r)
        out.SetPointError(p, exl, exh, dn, up)

    return out

def main():
    if len(sys.argv)!=4:
        print('usage: python genSF.py data_file mc_file out_file')
        return
    
    data_fname = sys.argv[1]
    mc_fname = sys.argv[2]
    out_fname = sys.argv[3]

    data_file = ROOT.TFile(data_fname)
    mc_file = ROOT.TFile(mc_fname)



    data_eff = data_file.Get("total_eff")
    mc_eff = mc_file.Get("total_eff")
    data_eff_qeta = data_file.Get("total_qeta_eff")
    mc_eff_qeta = mc_file.Get("total_qeta_eff")
    if not data_eff or not mc_eff:
        print('Data/MC pT eff. error')
        return
    if not data_eff_qeta or not mc_eff_qeta:
        print('Data/MC qEta eff. error')
        return
    
    print(f'{data_fname} + {mc_fname} -> {out_fname}')

    # SF = ratio_of_TGraphs(data_eff, mc_eff, 'scale_factor_pT')
    # SF_qeta = ratio_of_TGraphs(data_eff_qeta, mc_eff_qeta, 'scale_factor_qEta')
    SF = ratio_TGraphAsymmErrors(data_eff, mc_eff, 'scale_factor_pT')
    SF_qeta = ratio_TGraphAsymmErrors(data_eff_qeta, mc_eff_qeta, 'scale_factor_qEta')

    out_file = ROOT.TFile(out_fname, "RECREATE")
    SF.Write()
    SF_qeta.Write()
    out_file.Close()

    data_file.Close()
    mc_file.Close()

if __name__ == "__main__":
    main()