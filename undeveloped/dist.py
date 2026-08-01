import os
import pandas as pd
import numpy as np

from ase.io import read
from ase.neighborlist import mic


def find_poscars(root="."):
    files = []
    for path, dirs, names in os.walk(root):
        for name in names:
            if name.upper() == "POSCAR":
                files.append(os.path.join(path, name))
    return files


def calc_nb_distance(poscar):

    atoms = read(poscar)

    nb_idx = [i for i, s in enumerate(atoms.symbols) if s == "Nb"]

    if len(nb_idx) != 2:
        raise ValueError(f"{poscar}: Nb number={len(nb_idx)}")

    pos = atoms.positions[nb_idx]

    vec = pos[1] - pos[0]

    if atoms.pbc.any():
        vec = mic(vec, atoms.cell, atoms.pbc)

    return np.linalg.norm(vec)


def main():

    poscars = find_poscars(".")

    print(f"Found {len(poscars)} POSCAR")

    results = []

    for p in poscars:
        try:
            d = calc_nb_distance(p)

            results.append([p, d])

        except Exception as e:
            print("Skip:", p, e)

    df = pd.DataFrame(results, columns=["POSCAR", "Nb-Nb_distance_A"])

    # 按Nb-Nb距离从小到大排序
    df = df.sort_values(by="Nb-Nb_distance_A", ascending=True)

    # 重置编号
    df = df.reset_index(drop=True)

    df.to_csv("Nb_Nb_distance_sorted.csv", index=False)

    print("Saved: Nb_Nb_distance_sorted.csv")


if __name__ == "__main__":
    main()
