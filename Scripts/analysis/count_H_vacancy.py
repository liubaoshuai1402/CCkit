# CCkit 功能说明：
# 识别并统计结构或轨迹中的间隙氢原子。
import numpy as np
from ase.io import read 
from pymatgen.io.ase import AseAtomsAdaptor
import argparse

def countH(traj, r):
    structures = traj
    interstitialH_list = []
    for structure in structures:
        structure = AseAtomsAdaptor.get_structure(structure)
        interstitialH = 0
        for i, site in enumerate(structure):
            if site.specie.symbol != "H":
                continue
            Hneighbors = structure.get_neighbors(site,r)
            if Hneighbors == []:
                interstitialH = interstitialH + 1
        interstitialH_list.append(interstitialH)
    np.savetxt('count_H_vacancy.txt', np.array([interstitialH_list]).T, fmt='%d', header='Interstitial_H')
    interstitialH_avg = np.mean(interstitialH_list)
    np.savetxt('count_H_vacancy_avg.txt', np.array([[interstitialH_avg]]), fmt='%.2f', header='Interstitial_H_Avg')
def main():
    parser = argparse.ArgumentParser(description="count interstitial H atoms in structures.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("--r",type=float,default=1.8,help="The radius of the H atom is such that there are no other atoms nearby.")

    args = parser.parse_args()

    traj = read(args.input,':')
    countH(traj, args.r)

if __name__ == "__main__":
    main()
