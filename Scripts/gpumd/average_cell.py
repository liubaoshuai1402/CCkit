from ase.io import read,write
import numpy as np
import os
import argparse

def average_cell(nptdir):
    prim_path = os.path.join(nptdir,'model.xyz')
    prim = read(prim_path)
    thermo_path = os.path.join(nptdir,'thermo.out')
    thermo = np.loadtxt(thermo_path)
    atoms_temp = prim.copy()
    a = np.sum(thermo[:,9:12],axis=0)/len(thermo)
    b = np.sum(thermo[:,12:15],axis=0)/len(thermo)
    c = np.sum(thermo[:,15:18],axis=0)/len(thermo)
    cell_new = np.array([a,b,c])
    atoms_temp.set_cell(cell_new,scale_atoms=True)
    return atoms_temp

def main():
    parser = argparse.ArgumentParser(description="get average cell from thermo.out and write to model_temp.xyz")

    parser.add_argument("--nptdir", type=str, default='.',help="the directory run npt, default is .")

    args = parser.parse_args()

    atoms_temp = average_cell(args.nptdir)
    write_path = os.path.join(args.nptdir,'model_temp.xyz')
    write(write_path,atoms_temp)


if __name__ == "__main__":
    main()