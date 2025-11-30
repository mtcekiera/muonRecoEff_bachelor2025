import ROOT
import plotFunctions as pf

ID_MS_DATAFILE = "output/ID_MS/w0/hist_data23.root" 
MU_ID_DATAFILE = "output/mu_ID/w0/hist_data23.root" 

ID_MS_MCFILE = "output/ID_MS/w0/hist_mc_sc.root" 
MU_ID_MCFILE = "output/mu_ID/w0/hist_mc_sc.root" 


_H2D = [
    {
    'in_fname': ID_MS_DATAFILE,
    'h2_name': "aco_v_probe_pt_presel",
    'x_label':"#it{p}_{#it{T}}^{ID,exMS}",
    'y_label':"#it{a}_{#it{#phi}}^{ID,exMS}",
    'x_cuts': [2],
    'y_cuts': [0.02],
    'pdf_name':"paper/idms/aco_v_pairPt.pdf"},

    {
    'in_fname': MU_ID_DATAFILE,
    'h2_name': "aco_v_probe_pt_presel",
    'x_label':"#it{p}_{#it{T}}^{#it{#mu},ID}",
    'y_label':"#it{a}_{#it{#phi}}^{#it{#mu},ID}",
    'x_cuts': [2],
    'y_cuts': [0.02],
    'pdf_name':"paper/muid/aco_v_pairPt.pdf"
    },

    {
    'in_fname': ID_MS_DATAFILE,
    'h2_name': "dR_v_probe_pt_presel",
    'x_label': "#it{p}_{#it{T}}^{exMS}",
    'y_label': "#Delta#it{R}^{exMS,ID}",
    'y_cuts': [0.1],
    'pdf_name':"paper/idms/dr_v_probePt.pdf"
    },

    {
    'in_fname': MU_ID_DATAFILE,
    'h2_name': "dR_v_probe_pt_presel",
    'x_label': "#it{p}_{#it{T}}^{ID}",
    'y_label': "#Delta#it{R}^{#it{#mu},ID}",
    'y_cuts': [0.01],
    'pdf_name':"paper/muid/dr_v_probePt.pdf"
    }
]

_H1D = [
    {
        'h_name':       'probe_qEta_total',
        'output_pdf':   'probe_qEta_total.pdf',
        'xlabel-idms':  '#it{q#eta}^{exMS}',
        'xlabel-muid':  '#it{q#eta}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         False,
        'cut':          None
    },
    {   
        'h_name':       'probe_pt',
        'output_pdf':   'probe_pt.pdf',
        'xlabel-idms':  '#it{P}_{#it{T}}^{exMS}',
        'xlabel-muid':  '#it{P}_{#it{T}}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'probe_phi',
        'output_pdf':   'probe_phi.pdf',
        'xlabel-idms':  '#it{#phi}^{exMS}',
        'xlabel-muid':  '#it{#phi}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         False,
        'cut':          None
    },
    {
        'h_name':       'probe_eta',
        'output_pdf':   'probe_eta.pdf',
        'xlabel-idms':  '#eta^{exMS}',
        'xlabel-muid':  '#eta^{ID}',
        'ylabel':       'no. of probes',
        'logy':         False,
        'cut':          None
    },
    {
        'h_name':       'probe_pt_midsel',
        'output_pdf':   'probe_pt_midsel.pdf',
        'xlabel-idms':  '#it{p}_{#it{T}}^{exMS} [GeV]',
        'xlabel-muid':  '#it{p}_{#it{T}}^{ID} [GeV]',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'probe_d0_presel',
        'output_pdf':   'probe_d0_presel.pdf',
        'xlabel-idms':  '#it{d}_{0}^{exMS} [mm]',
        'xlabel-muid':  '#it{d}_{0}^{ID} [mm]',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'probe_dR_presel',
        'output_pdf':   'probe_dR_presel.pdf',
        'xlabel-idms':  '#it{dR}^{exMS}',
        'xlabel-muid':  '#it{dR}^{ID}',
        'ylabel':       'no. of probes',
        'logy':         True,
        'cut':          None
    },
    {
        'h_name':       'TPpair_aco_presel',
        'output_pdf':   'TPpair_aco_presel.pdf',
        'xlabel-idms':  '#it{A}_{#it{#phi}}^{#mu-exMS}',
        'xlabel-muid':  '#it{A}_{#it{#phi}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
        'cut':          0.02
    },
    {
        'h_name':       'TPpair_aco_midsel',
        'output_pdf':   'TPpair_aco_midsel.pdf',
        'xlabel-idms':  '#it{A}_{#it{#phi}}^{#mu-exMS}',
        'xlabel-muid':  '#it{A}_{#it{#phi}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
        'cut':          0.02
    },
    {
        'h_name':       'TPpair_pt_presel',
        'output_pdf':   'TPpair_pt_presel.pdf',
        'xlabel-idms':  '#it{p}_{#it{T}}^{#mu-exMS}',
        'xlabel-muid':  '#it{p}_{#it{T}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
        'cut':          2
    },
    {
        'h_name':       'TPpair_pt_postsel',
        'output_pdf':   'TPpair_pt_postsel.pdf',
        'xlabel-idms':  '#it{p}_{#it{T}}^{#mu-exMS}',
        'xlabel-muid':  '#it{p}_{#it{T}}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
        'cut':          2
    },
    {
        'h_name':       'TPpair_M_presel',
        'output_pdf':   'TPpair_M_presel.pdf',
        'xlabel-idms':  '#it{M}_{inv.}^{#mu-exMS}',
        'xlabel-muid':  '#it{M}_{inv.}^{#mu-ID}',
        'ylabel':       'no. of tag-probe pairs',
        'logy':         True,
        'cut':          None
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

    idms_h1d['data_file'] = ID_MS_DATAFILE
    idms_h1d['mc_file'] = ID_MS_MCFILE
    idms_h1d['output_pdf'] = 'paper/idms/' + idms_h1d['output_pdf']
    idms_h1d['xlabel'] = idms_h1d['xlabel-idms']
    idms_h1d.pop("xlabel-idms")
    idms_h1d.pop("xlabel-muid")

    muid_h1d['data_file'] = MU_ID_DATAFILE
    muid_h1d['mc_file'] = MU_ID_MCFILE
    muid_h1d['output_pdf'] = 'paper/muid/' + muid_h1d['output_pdf']
    muid_h1d['xlabel'] = muid_h1d['xlabel-muid']
    muid_h1d.pop("xlabel-idms")
    muid_h1d.pop("xlabel-muid")

    IDMS_H1D.append(idms_h1d)
    MUID_H1D.append(muid_h1d)


for kwargs in _H2D:
    pf.draw_2d_full(**kwargs)
for kwargs_idms, kwargs_muid in zip(IDMS_H1D, MUID_H1D):
    pf.plot_1d_histogram(**kwargs_idms)
    pf.plot_1d_histogram(**kwargs_muid)
