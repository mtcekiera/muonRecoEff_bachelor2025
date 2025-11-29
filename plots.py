import ROOT
import plotFunctions as pf

ID_MS_DATAFILE = "output/ID_MS/w0/hist_data23.root" 
MU_ID_DATAFILE = "output/mu_ID/w0/hist_data23.root" 

ID_MS_MCFILE = "output/ID_MS/w0/hist_mc_sc.root" 
MU_ID_MCFILE = "output/mu_ID/w0/hist_mc_sc.root" 


_H2D = [
    {
    'in_fname': ID_MS_DATAFILE,
    'h2_name': "aco_v_probe_pt_midsel",
    'x_label':"#it{p}_{#it{T}}^{ID,exMS}",
    'y_label':"#it{a}_{#it{#phi}}^{ID,exMS}",
    'x_cuts': [2],
    'y_cuts': [0.02],
    'pdf_name':"paper/aco_v_pairPt_idms.pdf"},

    {
    'in_fname': MU_ID_DATAFILE,
    'h2_name': "aco_v_probe_pt_midsel",
    'x_label':"#it{p}_{#it{T}}^{#it{#mu},ID}",
    'y_label':"#it{a}_{#it{#phi}}^{#it{#mu},ID}",
    'x_cuts': [2],
    'y_cuts': [0.02],
    'pdf_name':"paper/aco_v_pairPt_muid.pdf"
    },

    {
    'in_fname': ID_MS_DATAFILE,
    'h2_name': "dR_v_probe_pt_midsel",
    'x_label': "#it{p}_{#it{T}}^{exMS}",
    'y_label': "#Delta#it{R}^{exMS,ID}",
    'y_cuts': [0.1],
    'pdf_name':"paper/dr_v_probePt_idms.pdf"
    },

    {
    'in_fname': MU_ID_DATAFILE,
    'h2_name': "dR_v_probe_pt_midsel",
    'x_label': "#it{p}_{#it{T}}^{ID}",
    'y_label': "#Delta#it{R}^{#it{#mu},ID}",
    'y_cuts': [0.01],
    'pdf_name':"paper/dr_v_probePt_muid.pdf"
    }
]

_H1D = [
    {
        'data_file':    ID_MS_DATAFILE,
        'mc_file':      ID_MS_MCFILE,
        'h_name':       'probe_eta',
        'output_pdf':   'paper/probe_eta_idms.pdf',
        'xlabel':       '#eta',
        'ylabel':       'counts',
        # 'logy':         True
    }
]

# for kwargs in _H2D:
#     pf.draw_2d_full(**kwargs)
for kwargs in _H1D:
    pf.plot_1d_histogram(**kwargs)
