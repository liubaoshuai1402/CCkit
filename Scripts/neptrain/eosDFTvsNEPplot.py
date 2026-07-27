import numpy as np
import matplotlib.pyplot as plt
from ase.io import read
from calorine.calculators import CPUNEP
from pymatgen.analysis.eos import EOS
from matplotlib.ticker import MultipleLocator
import os
import argparse

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--eos",default=".",help="EOS directory")
    parser.add_argument("--nep",default="nep.txt",help="NEP potential file")
    parser.add_argument("--out",default="EOS_DFT_vs_NEP")
    args=parser.parse_args()

    calc=CPUNEP(args.nep)

    folders=sorted(
        [f for f in os.listdir(args.eos)
         if os.path.isdir(os.path.join(args.eos,f))],
        key=float
    )

    vol,dft,nep=[],[],[]
    atom_numbers = 1

    for f in folders:
        path=os.path.join(args.eos,f)

        outcar=os.path.join(path,"OUTCAR")
        if not os.path.exists(outcar):
            outcar+=".gz"
        atoms=read(outcar)
        vol.append(atoms.get_volume())
        dft.append(atoms.get_potential_energy())

        structure="CONTCAR" if os.path.exists(
            os.path.join(path,"CONTCAR")
        ) else "POSCAR"
        atoms=read(os.path.join(path,structure))
        atoms.calc=calc
        nep.append(atoms.get_potential_energy())
        atom_numbers = len(atoms)

    vol=np.array(vol)/atom_numbers
    dft=np.array(dft)/atom_numbers
    nep=np.array(nep)/atom_numbers

    fit_dft=EOS(eos_name="birch_murnaghan").fit(vol,dft)
    fit_nep=EOS(eos_name="birch_murnaghan").fit(vol,nep)

    print(
        f"DFT: V0={fit_dft.v0:.4f} A3, "
        f"B0={fit_dft.b0*160.2177:.2f} GPa, "
        f"E0={fit_dft.e0:.6f} eV/atom"
    )

    print(
        f"NEP: V0={fit_nep.v0:.4f} A3, "
        f"B0={fit_nep.b0*160.2177:.2f} GPa, "
        f"E0={fit_nep.e0:.6f} eV/atom"
    )

    v=np.linspace(min(vol),max(vol),200)

    plt.figure(figsize=(5,4))
    plt.scatter(vol,dft,label="DFT")
    plt.scatter(vol,nep,label="NEP")

    plt.plot(
        v,
        fit_dft(v),
        label="DFT EOS"
    )

    plt.plot(
        v,
        fit_nep(v),
        "--",
        label="NEP EOS"
    )

    plt.xlabel(r"Volume ($\AA^3$/atom)")
    plt.ylabel("Energy (eV/atom)")
    plt.legend()
    plt.tight_layout()

    plt.savefig(args.out+".png",dpi=600)

    np.savetxt(
        args.out+".txt",
        np.column_stack([vol,dft,nep]),
        header="Volume(A3/atom) DFT(eV/atom) NEP(eV/atom)",
        fmt="%.8f"
    )

if __name__=="__main__":
    main()