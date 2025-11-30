#define G2TauTree_cxx
#include "G2TauTree.h"

Float_t abs_t(Float_t x){
    if(x<0) return -1*x;
    return x;
}

G2TauTree::G2TauTree(std::string input_fname, std::string out_fname, bool TPType_, double sigma, int wp) : fChain(0) 
{
    TPType = TPType_;
    weight = 1.0;
    if(sigma>0.0){
        int N = 50000;
        double L = 1669.69; // [ub^-1]
        weight = L*sigma/N;
    }
    
    // wp:
    // 0 - initial analysis
    // 1 - tight wp
    // 2 - aco<0.01
    // 3 - aco<0.03
    // 4 - both zdc < 1 TeV
    // 5 - no d0 cuts
    save_all = false;
    if(wp==0)   save_all = true;

    wpTight = false;
    if(wp==1)  wpTight = true;

    check_zdc = false;
    if(wp==4)   check_zdc = true;

    check_d0 = true;
    if(wp==5)   check_d0 = false;

    TPpair_pt_threshold = 2;
    if(wp==6) TPpair_pt_threshold = 1;

    switch(wp){
        default:
            aco_threshold = 0.02;
            break;
        case 2:
            aco_threshold = 0.01;
            break;
        case 3:
            aco_threshold = 0.03;
    }

    output_fname = out_fname;
    std::cout<<"input: "<<input_fname<<"\n"<<"output: "<<output_fname<<std::endl;
    // 0 - ID|MS; 1 - mu|ID
    if(!TPType)
        std::cout<<"ID||MS analysis"<<std::endl;
    else
        std::cout<<"mu||ID analysis"<<std::endl;
    std::cout<<"wp = "<<wp<<std::endl;
    TTree * tree;
    TFile *f = (TFile*)gROOT->GetListOfFiles()->FindObject(input_fname.c_str());
    if (!f || !f->IsOpen()) {
        f = new TFile(input_fname.c_str());
    }
    f->GetObject("G2TauTree",tree);

    
    Init(tree);

    Loop();
}


void G2TauTree::Loop()
{
    if (fChain == 0) return;

    // commands for output
    TFile* output_file = new TFile(output_fname.c_str(), "RECREATE");

    TTree *output_tree = new TTree("G2TauTree_output", "Analysed G2TauTree data");


    // cutflow
    std::vector<Int_t> *eps_cutflow = new std::vector<Int_t>();

    Int_t TPpair_n;

    std::vector<Float_t> *tag_pt  = new std::vector<Float_t>();
    std::vector<Float_t> *tag_phi  = new std::vector<Float_t>();
    std::vector<Float_t> *tag_eta  = new std::vector<Float_t>();



    std::vector<Float_t> *probe_pt  = new std::vector<Float_t>();
    std::vector<Float_t> *probe_phi  = new std::vector<Float_t>();
    std::vector<Float_t> *probe_eta  = new std::vector<Float_t>();
    
    std::vector<Float_t> *probe_pt_presel  = new std::vector<Float_t>();
    std::vector<Float_t> *probe_pt_midsel  = new std::vector<Float_t>();
    std::vector<Float_t> *probe_pt_postsel  = new std::vector<Float_t>();

    std::vector<Float_t> *probe_phi_presel  = new std::vector<Float_t>();
    std::vector<Float_t> *probe_phi_postsel  = new std::vector<Float_t>();
    
    std::vector<Float_t> *probe_eta_presel  = new std::vector<Float_t>();
    std::vector<Float_t> *probe_eta_postsel  = new std::vector<Float_t>();
    
    std::vector<Float_t> *probe_d0_presel = new std::vector<Float_t>();
    std::vector<Float_t> *probe_d0_postsel = new std::vector<Float_t>();
    
    std::vector<Float_t> *probe_dR_presel = new std::vector<Float_t>();
    std::vector<Float_t> *probe_dR_midsel = new std::vector<Float_t>();


    std::vector<Float_t> *eps_pass = new std::vector<Float_t>(); 
    std::vector<Float_t> *eps_qEta_pass = new std::vector<Float_t>();
    std::vector<Float_t> *eps_total = new std::vector<Float_t>();
    std::vector<Float_t> *eps_qEta_total = new std::vector<Float_t>();

    std::vector<Float_t> *TPpair_pt_presel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_pt_midsel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_pt_postsel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_M_presel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_M_postsel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_aco_presel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_aco_midsel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_dR_presel = new std::vector<Float_t>();
    std::vector<Float_t> *TPpair_dR_postsel = new std::vector<Float_t>();



    if(save_all){
        output_tree->Branch("eps_cutflow", &eps_cutflow);

        output_tree->Branch("TPpair_n", &TPpair_n);

        output_tree->Branch("tag_pt", &tag_pt);
        output_tree->Branch("tag_phi", &tag_phi);
        output_tree->Branch("tag_eta", &tag_eta);


        output_tree->Branch("probe_pt_presel", &probe_pt_presel);
        output_tree->Branch("probe_pt_midsel", &probe_pt_midsel); 
        output_tree->Branch("probe_pt_postsel", &probe_pt_postsel);

        output_tree->Branch("probe_eta", &probe_eta);
        output_tree->Branch("probe_phi", &probe_phi);
        output_tree->Branch("probe_pt", &probe_pt);
        
        output_tree->Branch("probe_phi_presel", &probe_phi_presel);
        output_tree->Branch("probe_phi_postsel", &probe_phi_postsel);
        
        output_tree->Branch("probe_eta_presel", &probe_eta_presel);
        output_tree->Branch("probe_eta_postsel", &probe_eta_postsel);
        
        output_tree->Branch("probe_d0_presel", &probe_d0_presel);
        output_tree->Branch("probe_d0_postsel", &probe_d0_postsel);
        
        output_tree->Branch("probe_dR_presel", &probe_dR_presel);
        output_tree->Branch("probe_dR_midsel", &probe_dR_midsel);


        output_tree->Branch("TPpair_pt_presel", &TPpair_pt_presel);
        output_tree->Branch("TPpair_pt_midsel", &TPpair_pt_midsel);
        output_tree->Branch("TPpair_pt_postsel", &TPpair_pt_postsel);

        output_tree->Branch("TPpair_dR_presel", &TPpair_dR_presel);
        output_tree->Branch("TPpair_dR_postsel", &TPpair_dR_postsel);

        output_tree->Branch("TPpair_M_presel", &TPpair_M_presel);
        output_tree->Branch("TPpair_M_postsel", &TPpair_M_postsel);

        output_tree->Branch("TPpair_aco_presel", &TPpair_aco_presel);
        output_tree->Branch("TPpair_aco_midsel", &TPpair_aco_midsel);
    }

    output_tree->Branch("weight", &weight);
    output_tree->Branch("eps_pass", &eps_pass);
    output_tree->Branch("eps_qEta_pass", &eps_qEta_pass);
    output_tree->Branch("eps_total", &eps_total);
    output_tree->Branch("eps_qEta_total", &eps_qEta_total);

    int checkpoint = 10000;
    Long64_t nentries = fChain->GetEntriesFast();
    Long64_t nbytes = 0, nb = 0;

    //////////////////  LOOP    /////////////////////////
    for (Long64_t jentry=0; jentry<nentries;jentry++) 
    {
        
        Long64_t ientry = LoadTree(jentry);
        if (ientry < 0) break;
        nb = fChain->GetEntry(jentry);   nbytes += nb;

        if(jentry%checkpoint==0){
            std::cout<<"\ranalysing entry no. "<<jentry<<" / "<<nentries<<std::flush;
        }

        ///// CLEARING VECTORS
        eps_cutflow->clear();

        TPpair_n = 0;

        tag_pt->clear();
        tag_phi->clear();
        tag_eta->clear();

        probe_pt->clear();
        probe_phi->clear();
        probe_eta->clear();

        probe_phi_presel->clear();
        probe_phi_postsel->clear();
        
        probe_eta_presel->clear();
        probe_eta_postsel->clear();
        
        probe_pt_presel->clear();
        probe_pt_midsel->clear();
        probe_pt_postsel->clear();

        probe_d0_presel->clear();
        probe_d0_postsel->clear();

        probe_dR_presel->clear();
        probe_dR_midsel->clear();


        TPpair_aco_presel->clear();
        TPpair_aco_midsel->clear();

        TPpair_pt_presel->clear();
        TPpair_pt_midsel->clear();
        TPpair_pt_postsel->clear();

        TPpair_dR_presel->clear();
        TPpair_dR_postsel->clear();
        
        TPpair_M_presel->clear();
        TPpair_M_postsel->clear();


        eps_pass->clear(); 
        eps_qEta_pass->clear();
        eps_total->clear();
        eps_qEta_total->clear();

        ////// EO CLEARING VECTORS

        //eps
        eps_cutflow->push_back(0);

        //passes GRL: all data from file does
        if(!passed_HLT_mu3_hi_FgapAC5_L1MU3V_VTE50){
            output_tree->Fill();
            continue;
        }
        eps_cutflow->push_back(1);

        if(check_zdc)
        if(!(zdc_ene_a<1e3 || zdc_ene_c<1e3)){
            output_tree->Fill();
            continue;
        }
        eps_cutflow->push_back(2);
        //at least 1 muon

        if(!(nMuon >= 1)){
            output_tree->Fill();
            continue;
        } 
        eps_cutflow->push_back(3);
        // up to 2 tracks
        // if(!(track_n<=2))
        
        if(!(track_n==2 || track_n==1))
        {
            output_tree->Fill();
            continue;
        } 
        eps_cutflow->push_back(4);

        //finding tag
        for(int tag = 0; tag<nMuon; tag++)
        {
            // if(!(muon_is_Loose->at(tag))) continue;
            if(wpTight){
                if(!(muon_is_Tight->at(tag))) continue;
            }
            else{
                if(!(muon_is_LowPt->at(tag))) continue; // is_LowPt should have the Loose working point
            }
            if(!(abs(muon_eta->at(tag))<2.4)) continue;
            if(!(muon_pt->at(tag)>3)) continue;
            if(check_d0){if(!(abs(muon_d0->at(tag))<2)) continue;}
            
            tag_pt->push_back(muon_pt->at(tag));
            tag_phi->push_back(muon_phi->at(tag));
            tag_eta->push_back(muon_eta->at(tag));

            /////////////////// finding ID||MS probes /////////////////////////////////////

            int MSmuon_n = MSmuon_d0->size();
            if(!TPType) if(!(MSmuon_n==2)) continue;
            if(!TPType) for(int probe = 0; probe<MSmuon_n; probe++)
            { 
                TLorentzVector v_tag, v_probe, v_pair; 
                v_tag.SetPtEtaPhiM(muon_pt->at(tag), muon_eta->at(tag), muon_phi->at(tag), M_mu);
                v_probe.SetPtEtaPhiM(MSmuon_pt->at(probe), MSmuon_eta->at(probe), MSmuon_phi->at(probe), M_mu);
                v_pair = v_tag+v_probe;
                double aco = 1-abs(v_tag.DeltaPhi(v_probe))/TMath::Pi();
                double tp_dR = v_probe.DeltaR(v_tag);
                
            
                // distributions before any selections
                probe_d0_presel->push_back(MSmuon_d0->at(probe));
                probe_phi_presel->push_back(MSmuon_phi->at(probe));
                probe_eta_presel->push_back(MSmuon_eta->at(probe));


                TPpair_dR_presel->push_back(tp_dR);
                TPpair_M_presel->push_back(v_pair.M());
                // aco-pair pt corr. plots (before any cuts)
                TPpair_pt_presel->push_back(v_pair.Pt());
                TPpair_aco_presel->push_back(aco);


                if(check_d0){if(!(abs(MSmuon_d0->at(probe))<2)) continue;}


                // aco-pair pt corr. plots (after cuts, before aco/dr cuts)
                TPpair_pt_midsel->push_back(v_pair.Pt());
                TPpair_aco_midsel->push_back(aco);

                if(!(v_pair.Pt()<TPpair_pt_threshold)) continue;
                if(!(aco<aco_threshold)) continue;
                if(!(muon_charge->at(tag) * MSmuon_charge->at(probe) < 0))

                probe_eta->push_back(MSmuon_eta->at(probe));
                probe_phi->push_back(MSmuon_phi->at(probe));
                probe_pt->push_back(MSmuon_pt->at(probe));
                
                eps_total->push_back(MSmuon_pt->at(probe));
                eps_qEta_total->push_back(MSmuon_eta->at(probe)*MSmuon_charge->at(probe));

                for(int id = 0; id<track_n; id++)
                {
                    TLorentzVector v_id;
                    v_id.SetPtEtaPhiM(track_pt->at(id), track_eta->at(id), track_phi->at(id), M_mu);
                    double probe_dR = v_probe.DeltaR(v_id);

                    // dR - probe pt corr. plot
                    probe_pt_presel->push_back(MSmuon_pt->at(probe));
                    probe_dR_presel->push_back(probe_dR);

                    if(!(track_is_LooseMuon->at(id))) continue; 
                    if(check_d0){if(!(abs(track_d0->at(id))<2)) continue;}

                    // dR - probe pt corr. plot
                    probe_pt_midsel->push_back(MSmuon_pt->at(probe));
                    probe_dR_midsel->push_back(probe_dR);

                    if(!(probe_dR<0.1)) continue;

                    TPpair_n++;

                    probe_phi_postsel->push_back(MSmuon_phi->at(probe));
                    probe_eta_postsel->push_back(MSmuon_eta->at(probe));
                    probe_pt_postsel->push_back(MSmuon_pt->at(probe));

                    TPpair_M_postsel->push_back(v_pair.M());
                    probe_d0_postsel->push_back(MSmuon_d0->at(probe));
                    TPpair_dR_postsel->push_back(tp_dR);
                    TPpair_pt_postsel->push_back(v_pair.Pt());

                    eps_pass->push_back(MSmuon_pt->at(probe));
                    eps_qEta_pass->push_back((MSmuon_eta->at(probe))*(MSmuon_charge->at(probe)));

                }
            }
            /////////////////// finding mu||ID probes /////////////////////////////////////
            else for(int probe = 0; probe<track_n; probe++)
            {
                TLorentzVector v_tag, v_probe, v_pair; 
                v_tag.SetPtEtaPhiM(muon_pt->at(tag), muon_eta->at(tag), muon_phi->at(tag), M_mu);
                v_probe.SetPtEtaPhiM(track_pt->at(probe), track_eta->at(probe), track_phi->at(probe), M_mu);
                v_pair = v_tag+v_probe;
                double aco = 1-abs(v_tag.DeltaPhi(v_probe))/TMath::Pi();
                double tp_dR = v_probe.DeltaR(v_tag);
                
            
                // distributions before any selections
                probe_d0_presel->push_back(track_d0->at(probe));
                probe_phi_presel->push_back(track_phi->at(probe));
                probe_eta_presel->push_back(track_eta->at(probe));

                TPpair_dR_presel->push_back(tp_dR);
                TPpair_M_presel->push_back(v_pair.M());
                // aco - pair pt corr.
                TPpair_pt_presel->push_back(v_pair.Pt());
                TPpair_aco_presel->push_back(aco);

                if(!(muon_charge->at(tag)*track_charge->at(probe)<0)) continue;
                if(!(track_is_LooseMuon->at(probe))) continue;
                if(check_d0){if(!(abs(track_d0->at(probe))<2)) continue;}

                // aco - pair pt correlation
                TPpair_pt_midsel->push_back(v_pair.Pt());
                TPpair_aco_midsel->push_back(aco);

                if(!(v_pair.Pt()<TPpair_pt_threshold)) continue;
                if(!(aco<aco_threshold)) continue;

                probe_eta->push_back(track_eta->at(probe));
                probe_phi->push_back(track_phi->at(probe));
                probe_pt->push_back(track_pt->at(probe));


                eps_qEta_total->push_back((track_eta->at(probe))*(track_charge->at(probe)));
                eps_total->push_back(track_pt->at(probe));

                for(int m_LPt = 0; m_LPt < nMuon; m_LPt++)
                {
                    TLorentzVector v_m_LPt;
                    v_m_LPt.SetPtEtaPhiM(muon_pt->at(m_LPt), muon_eta->at(m_LPt), muon_phi->at(m_LPt), M_mu);

                    double probe_dR = v_probe.DeltaR(v_m_LPt);
                    // dR - probe pt corr.
                    probe_pt_presel->push_back(track_pt->at(probe));
                    probe_dR_presel->push_back(probe_dR);

                    if(wpTight){
                        if(!(muon_is_Tight->at(m_LPt))) continue;
                    }
                    else{
                        if(!(muon_is_LowPt->at(m_LPt))) continue; // nie is_loose?
                    }

                    // dR - probe pt corr.
                    probe_pt_midsel->push_back(track_pt->at(probe));
                    probe_dR_midsel->push_back(probe_dR);

                    if(!(probe_dR<0.01)) continue;



                    TPpair_n++;

                    probe_pt_postsel->push_back(track_pt->at(probe));
                    probe_phi_postsel->push_back(track_phi->at(probe));
                    probe_eta_postsel->push_back(track_eta->at(probe));

                    TPpair_M_postsel->push_back(v_pair.M());
                    TPpair_dR_postsel->push_back(tp_dR);
                    probe_d0_postsel->push_back(track_d0->at(probe));
                    TPpair_pt_postsel->push_back(v_pair.Pt());

                    eps_pass->push_back(track_pt->at(probe));
                    eps_qEta_pass->push_back((track_eta->at(probe))*(track_charge->at(probe)));
                    
                }
            }
        }
        if(!TPpair_n){
            output_tree->Fill();
            continue;
        } 
        eps_cutflow->push_back(5);

        

        output_tree->Fill();

    }
    ////////// END OF LOOP //////////////
    std::cout<<"\ranalysing entry no. "<<nentries<<" / "<<nentries<<std::flush;
    std::cout<<std::endl;
    std::cout<<"[ DONE ]"<<std::endl;


    // writing the histograms
    // output_file->Write();

    // cutflows
    delete eps_cutflow;

    delete eps_pass; 
    delete eps_total;
    delete eps_qEta_pass;
    delete eps_qEta_total;

    delete TPpair_pt_presel;
    delete TPpair_pt_midsel;
    delete TPpair_pt_postsel;
    delete TPpair_M_presel;
    delete TPpair_M_postsel;
    delete TPpair_dR_presel;
    delete TPpair_dR_postsel;
    delete TPpair_aco_presel;
    delete TPpair_aco_midsel;

    delete tag_pt;
    delete tag_eta;
    delete tag_phi;


    delete probe_pt;
    delete probe_phi;
    delete probe_eta;

    delete probe_pt_presel;
    delete probe_pt_midsel;
    delete probe_pt_postsel;

    delete probe_eta_presel;
    delete probe_eta_postsel;

    delete probe_phi_presel;
    delete probe_phi_postsel;

    delete probe_d0_presel;
    delete probe_d0_postsel;

    delete probe_dR_presel;
    delete probe_dR_midsel;


    output_tree->Write();
    output_file->Close();
}

