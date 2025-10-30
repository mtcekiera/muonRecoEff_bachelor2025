import ROOT
import numpy as np

f = ROOT.TFile("./output/ID_MS/data23.root")

t = f.Get("G2TauTree_output")

nentries = t.GetEntries()
j = 0
pt = []
phi = []
eta = []
for event in t:
    if j % 10000 == 0:
        print(f"\rProgress: {j} / {nentries}", end="", flush=True)
    if(event.TPpair_n==2):
        pt.append((event.tag_pt[0]-event.probe_pt[1])/event.tag_pt[0])
        pt.append((event.tag_pt[1]-event.probe_pt[0])/event.tag_pt[1])
        phi.append((event.tag_phi[0]-event.probe_phi[1])/event.tag_phi[0])
        phi.append((event.tag_phi[1]-event.probe_phi[0])/event.tag_phi[1])
        eta.append((event.tag_eta[0]-event.probe_eta[1])/event.tag_eta[0])
        eta.append((event.tag_eta[1]-event.probe_eta[0])/event.tag_eta[1])
    j+=1
    # if(n>1e4):
        # break
print(f"\rProgress: {nentries} / {nentries}", end="", flush=True)
print()
print("Average relative differences:")

print(f"d_pt = {np.abs(np.average(pt)):.2g} +- {np.std(pt):.2g}")
print(f"d_phi = {np.abs(np.average(phi)):.2g} +- {np.std(phi):.2g}")
print(f"d_dta = {np.abs(np.average(eta)):.2g} +- {np.std(eta):.2g}")
