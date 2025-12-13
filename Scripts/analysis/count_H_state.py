import numpy as np
from ase.io import read 
from pymatgen.io.ase import AseAtomsAdaptor
import argparse

def countH(traj, OHdist, r):
    structures = traj
    bondedH_list = []
    interstitialH_list = []
    transitiveH_list = []
    for structure in structures:
        structure = AseAtomsAdaptor.get_structure(structure)
        bondedH = 0
        interstitialH = 0
        transitiveH = 0
        for i, site in enumerate(structure):
            if site.specie.symbol != "H":
                continue
            count = 0
            Hneighbors = structure.get_neighbors(site,OHdist)
            for Hneighbor in Hneighbors:
                if Hneighbor.specie.symbol == 'O':
                    bondedH = bondedH + 1
                    count = count + 1
                    break
            if count == 1:
                continue
            Hneighbors = structure.get_neighbors(site,r)
            if Hneighbors == []:
                interstitialH = interstitialH + 1
                continue
            if count == 0:
                transitiveH = transitiveH + 1
        bondedH_list.append(bondedH)
        interstitialH_list.append(interstitialH)
        transitiveH_list.append(transitiveH)
    np.savetxt('count_H_state.txt', np.array([bondedH_list, interstitialH_list, transitiveH_list]).T, fmt='%d', header='Bonded_H Interstitial_H Transitive_H')
    bondedH_avg = np.mean(bondedH_list)
    interstitialH_avg = np.mean(interstitialH_list)
    transitiveH_avg = np.mean(transitiveH_list)
    np.savetxt('count_H_state_avg.txt', np.array([[bondedH_avg, interstitialH_avg, transitiveH_avg]]), fmt='%.2f', header='Bonded_H_Avg Interstitial_H_Avg Transitive_H_Avg')

def main():
    parser = argparse.ArgumentParser(description="Single point calculation generator for vasp.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("--OHdist",type=float,default=1.2,help="set the max O-H bond distance")
    parser.add_argument("--r",type=float,default=2.0,help="The radius of the H atom is such that there are no other atoms nearby.")

    args = parser.parse_args()

    traj = read(args.input,':')
    countH(traj, args.OHdist, args.r)

if __name__ == "__main__":
    main()

