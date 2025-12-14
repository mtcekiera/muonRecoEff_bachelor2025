import ROOT
import plotFunctions as pf

IDMS_DATA_FNAME = "output/ID_MS/w0/hist_data23.root" 
MUID_DATA_FNAME = "output/mu_ID/w0/hist_data23.root" 

IDMS_MC_FNAME = "output/ID_MS/w0/hist_mc_sc.root" 
MUID_MC_FNAME = "output/mu_ID/w0/hist_mc_sc.root" 

EFF_DATA_FNAME = "output/eff/w0/eff_data23.root" 
EFF_MC_FNAME = "output/eff/w0/eff_mc_sc.root" 


_H2D = [
    {
    'in_fname': IDMS_DATA_FNAME,
    'h2_name': "aco_v_probe_pt_presel",
    'x_label':"#it{p}_{#it{T}}^{ID,exMS}",
    'y_label':"#it{a}_{#it{#phi}}^{ID,exMS}",
    'x_cuts': [2],
    'y_cuts': [0.02],
    'logz':     True,
    'pdf_name':"paper/idms/aco_v_pairPt.pdf"},

    {
    'in_fname': MUID_DATA_FNAME,
    'h2_name': "aco_v_probe_pt_presel",
    'x_label':"#it{p}_{#it{T}}^{#it{#mu},ID}",
    'y_label':"#it{a}_{#it{#phi}}^{#it{#mu},ID}",
    'x_cuts': [2],
    'y_cuts': [0.02],
    'logz':     True,
    'pdf_name':"paper/muid/aco_v_pairPt.pdf"
    },

    {
    'in_fname': IDMS_DATA_FNAME,
    'h2_name': "dR_v_probe_pt_presel",
    'x_label': "#it{p}_{#it{T}}^{exMS}",
    'y_label': "#Delta#it{R}^{exMS,ID}",
    'y_cuts': [0.1],
    'logz':     True,
    'pdf_name':"paper/idms/dr_v_probePt.pdf"
    },

    {
    'in_fname': MUID_DATA_FNAME,
    'h2_name': "dR_v_probe_pt_presel",
    'x_label': "#it{p}_{#it{T}}^{ID}",
    'y_label': "#Delta#it{R}^{#it{#mu},ID}",
    'y_cuts': [0.01],
    'logz':     True,
    'pdf_name':"paper/muid/dr_v_probePt.pdf"
    },

    {
    'in_fname': "output/eff/w0/sf_sc.root",
    'h2_name': "scale_factor_2d",
    'x_label': "#it{p}_{#it{T}}^{probe}",
    'y_label': "q#eta",
    'y_cuts': None,
    'logx': True,
    # 'logz': True,
    'pdf_name':"paper/sf/sf_2d.pdf",
    'text': True,
    'tight_layout': True,
    'canvas_size': (1200, 800)
    },
    {
    'in_fname': "output/eff/w0/eff_mc_sc.root",
    'h2_name': "total_2d_eff",
    'x_label': "#it{p}_{#it{T}}^{probe}",
    'y_label': "q#eta",
    'y_cuts': None,
    'logx': True,
    # 'logz': True,
    'pdf_name':"paper/eff/data_total_2d_eff.pdf",
    'text': True,
    'tight_layout': True,
    'canvas_size': (1200, 800)
    },
    {
    'in_fname': "output/eff/w0/eff_data23.root",
    'h2_name': "total_2d_eff",
    'x_label': "#it{p}_{#it{T}}^{probe}",
    'y_label': "q#eta",
    'y_cuts': None,
    'logx': True,
    # 'logz': True,
    'pdf_name':"paper/eff/sc_total_2d_eff.pdf",
    'text': True,
    'tight_layout': True,
    'canvas_size': (1200, 800)
    }
]

_H1D = [
    {   
        'h_name':       'tag_pt',
        'output_pdf':   'tag_pt.pdf',
        'xlabel-idms':  '#it{P}_{#it{T}}^{#mu}',
        'xlabel-muid':  '#it{P}_{#it{T}}^{#mu}',
        'ylabel':       'no. of tags',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'tag_phi',
        'output_pdf':   'tag_phi.pdf',
        'xlabel-idms':  '#it{#phi}^{#mu}',
        'xlabel-muid':  '#it{#phi}^{#mu}',
        'ylabel':       'no. of tags',
        'logy':         False,
        'cut':          None
    },
    {
        'h_name':       'tag_eta',
        'output_pdf':   'tag_eta.pdf',
        'xlabel-idms':  '#eta^{#mu}',
        'xlabel-muid':  '#eta^{#mu}',
        'ylabel':       'no. of tags',
        'logy':         False,
        'cut':          None
    },
    {
        'h_name':       'eps_qEta_pass',
        'output_pdf':   'eps_qEta_pass.pdf',
        'xlabel-idms':  '#it{q#eta}^{exMS}',
        'xlabel-muid':  '#it{q#eta}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         False,
        'cut':          None
    },
    {   
        'h_name':       'probe_pt_postsel',
        'output_pdf':   'probe_pt_postsel.pdf',
        'xlabel-idms':  '#it{P}_{#it{T}}^{exMS}',
        'xlabel-muid':  '#it{P}_{#it{T}}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'probe_phi_postsel',
        'output_pdf':   'probe_phi_postsel.pdf',
        'xlabel-idms':  '#it{#phi}^{exMS}',
        'xlabel-muid':  '#it{#phi}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         False,
        'cut':          None
    },
    {
        'h_name':       'probe_eta_postsel',
        'output_pdf':   'probe_eta_postsel.pdf',
        'xlabel-idms':  '#eta^{exMS}',
        'xlabel-muid':  '#eta^{ID}',
        'ylabel':       'no. of probes',
        'logy':         False,
        'cut':          None
    },
    {
        'h_name':       'probe_d0_postsel',
        'output_pdf':   'probe_d0_postsel.pdf',
        'xlabel-idms':  '#it{d}_{0}^{exMS} [mm]',
        'xlabel-muid':  '#it{d}_{0}^{ID} [mm]',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'probe_dR_postsel',
        'output_pdf':   'probe_dR_postsel.pdf',
        'xlabel-idms':  '#Delta#it{R}^{exMS-ID}',
        'xlabel-muid':  '#Delta#it{R}^{ID-#mu}',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        # 'h_name':       'probe_dR_postsel_shortrange',
        'h_name':       'dR_probe_postsel_shortrange',
        'output_pdf':   'probe_dR_postsel_shortrange.pdf',
        'xlabel-idms':  '#Delta#it{R}^{exMS-ID}',
        'xlabel-muid':  '#Delta#it{R}^{ID-#mu}',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'TPpair_aco_postsel',
        'output_pdf':   'TPpair_aco_postsel.pdf',
        'xlabel-idms':  '#it{A}_{#it{#phi}}^{#mu-exMS}',
        'xlabel-muid':  '#it{A}_{#it{#phi}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
    },
    {
        'h_name':       'TPpair_aco_postsel',
        'output_pdf':   'TPpair_aco_postsel.pdf',
        'xlabel-idms':  '#it{A}_{#it{#phi}}^{#mu-exMS}',
        'xlabel-muid':  '#it{A}_{#it{#phi}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
    },
    {
        'h_name':       'TPpair_pt_postsel',
        'output_pdf':   'TPpair_pt_postsel.pdf',
        'xlabel-idms':  '#it{p}_{#it{T}}^{#mu-exMS}',
        'xlabel-muid':  '#it{p}_{#it{T}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
    },
    {
        'h_name':       'TPpair_pt_postsel',
        'output_pdf':   'TPpair_pt_postsel.pdf',
        'xlabel-idms':  '#it{p}_{#it{T}}^{#mu-exMS}',
        'xlabel-muid':  '#it{p}_{#it{T}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
    },
    {
        'h_name':       'TPpair_M_postsel',
        'output_pdf':   'TPpair_M_postsel.pdf',
        'xlabel-idms':  '#it{M}_{inv.}^{#mu-exMS}',
        'xlabel-muid':  '#it{M}_{inv.}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
        'cut':          None
    },
]
IDMS_H1D = []
MUID_H1D = []
 
for h1d in _H1D:
    idms_h1d = h1d.copy()
    muid_h1d = h1d.copy()

    idms_h1d['data_fname'] = IDMS_DATA_FNAME
    idms_h1d['mc_fname'] = IDMS_MC_FNAME
    idms_h1d['output_pdf'] = 'paper/idms/' + idms_h1d['output_pdf']
    idms_h1d['xlabel'] = idms_h1d['xlabel-idms']
    idms_h1d.pop("xlabel-idms")
    idms_h1d.pop("xlabel-muid")

    muid_h1d['data_fname'] = MUID_DATA_FNAME
    muid_h1d['mc_fname'] = MUID_MC_FNAME
    muid_h1d['output_pdf'] = 'paper/muid/' + muid_h1d['output_pdf']
    muid_h1d['xlabel'] = muid_h1d['xlabel-muid']
    muid_h1d.pop("xlabel-idms")
    muid_h1d.pop("xlabel-muid")

    IDMS_H1D.append(idms_h1d)
    MUID_H1D.append(muid_h1d)

_EFF = [
    {
        'data_fname':   EFF_DATA_FNAME,
        'mc_fname':     EFF_MC_FNAME,
        'output_pdf':   'paper/eff/ID_MS_eff.pdf',
        'obj_name':     'ID_MS_eff',
        'ylim':         (0.95, 1.05),
        'logx':         True,
        'xlabel':       '#it{p}_{#it{T}} [GeV]',
        'ylabel':       '#it{#varepsilon}(ID|MS)'
    },
    {
        'data_fname':   EFF_DATA_FNAME,
        'mc_fname':     EFF_MC_FNAME,
        'output_pdf':   'paper/eff/mu_ID_eff.pdf',
        'obj_name':     'mu_ID_eff',
        'logx':         True,
        'xlabel':       '#it{p}_{#it{T}} [GeV]',
        'ylabel':       '#it{#varepsilon}(#mu|ID)'
    },
    {
        'data_fname':   EFF_DATA_FNAME,
        'mc_fname':     EFF_MC_FNAME,
        'output_pdf':   'paper/eff/total_eff.pdf',
        'obj_name':     'total_eff',
        'logx':         True,
        'xlabel':       '#it{p}_{#it{T}} [GeV]',
        'ylabel':       '#it{#varepsilon}(#mu)'
    },
    {
        'data_fname':   EFF_DATA_FNAME,
        'mc_fname':     EFF_MC_FNAME,
        'output_pdf':   'paper/eff/ID_MS_qEta_eff.pdf',
        'obj_name':     'ID_MS_qeta_eff',
        'ylim':         (0.95, 1.05),
        'logx':         False,
        'xlabel':       '#it{q#eta}',
        'ylabel':       '#it{#varepsilon}(ID|MS)'
    },
    {
        'data_fname':   EFF_DATA_FNAME,
        'mc_fname':     EFF_MC_FNAME,
        'output_pdf':   'paper/eff/mu_ID_qEta_eff.pdf',
        'obj_name':     'mu_ID_qeta_eff',
        'logx':         False,
        'xlabel':       '#it{q#eta}',
        'ylabel':       '#it{#varepsilon}(#mu|ID)'
    },
    {
        'data_fname':   EFF_DATA_FNAME,
        'mc_fname':     EFF_MC_FNAME,
        'output_pdf':   'paper/eff/total_qEta_eff.pdf',
        'obj_name':     'total_qeta_eff',
        'logx':         False,
        'xlabel':       '#it{q#eta}',
        'ylabel':       '#it{#varepsilon}(#mu)'
    }
]

# FOLDERS  = ["w0", "w1", "w2", "w3", "w4", "w5", "w6"]

_SC_WP = [
    {
        'in_fname': 'sf_sc.root', 
        'out_pdf':  'paper/sf/sf_sc_pt_wp.pdf', 
        'pT':       True,
        'sum_unc':  False
    },
    {
        'in_fname': 'sf_sc.root', 
        'out_pdf':  'paper/sf/sf_sc_pt_syst.pdf', 
        'pT':       True,
        'sum_unc':  True
    },
    {
        'in_fname': 'sf_sc.root', 
        'out_pdf':  'paper/sf/sf_sc_qeta_wp.pdf', 
        'pT':       False,
        'sum_unc':  False
    },
    {
        'in_fname': 'sf_sc.root', 
        'out_pdf':  'paper/sf/sf_sc_qeta_syst.pdf', 
        'pT':       False,
        'sum_unc':  True
    }
]

folders  = ["w0", "w7"]
labels = ["track is matched to muon", "track is loose muon"]

_SC_WP_COMPARISON = [
    {
        'in_fname': 'sf_sc.root', 
        'out_pdf':  'paper/loose_vs_ismatched/sf_sc_pt_wp.pdf', 
        'pT':       True,
        'sum_unc':  False,
        'folders':  folders,
        'labels':   labels
    },
    {
        'in_fname': 'sf_sc.root', 
        'out_pdf':  'paper/loose_vs_ismatched/sf_sc_qeta_wp.pdf', 
        'pT':       False,
        'sum_unc':  False,
        'folders':  folders,
        'labels':   labels
    },
    {
        'in_fname': 'sf_sl.root', 
        'out_pdf':  'paper/loose_vs_ismatched/sf_sl_pt_wp.pdf', 
        'pT':       True,
        'sum_unc':  False,
        'folders':  folders,
        'labels':   labels
    },
    {
        'in_fname': 'sf_sl.root', 
        'out_pdf':  'paper/loose_vs_ismatched/sf_sl_qeta_wp.pdf', 
        'pT':       False,
        'sum_unc':  False,
        'folders':  folders,
        'labels':   labels
    },
    {
        'in_fname': 'sf_mg.root', 
        'out_pdf':  'paper/loose_vs_ismatched/sf_mg_pt_wp.pdf', 
        'pT':       True,
        'sum_unc':  False,
        'folders':  folders,
        'labels':   labels
    },
    {
        'in_fname': 'sf_mg.root', 
        'out_pdf':  'paper/loose_vs_ismatched/sf_mg_qeta_wp.pdf', 
        'pT':       False,
        'sum_unc':  False,
        'folders':  folders,
        'labels':   labels
    }
]

# for kwargs in _H2D:
#     pf.plot_2d_histogram(**kwargs)
# for kwargs_idms, kwargs_muid in zip(IDMS_H1D, MUID_H1D):
#     pf.plot_1d_histogram(**kwargs_idms)
#     pf.plot_1d_histogram(**kwargs_muid)
for kwargs in _EFF:
    pf.plot_efficiency(**kwargs)
# for kwargs in _SC_WP:
    # pf.plot_scale_factor(**kwargs)
# for kwargs in _SC_WP_COMPARISON:
#     pf.plot_scale_factor(**kwargs)