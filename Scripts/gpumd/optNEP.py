import argparse,os
import numpy as np
from ase.io import read,write
from ase.io.vasp import write_vasp
from calorine.calculators import CPUNEP
from calorine.tools import relax_structure

def main():
    parser=argparse.ArgumentParser(description="NEP structure relaxation")
    parser.add_argument("-i","--structure",default='POSCAR')
    parser.add_argument("--nep",default="nep.txt")
    parser.add_argument("--opt",default="fire")
    parser.add_argument("--steps",type=int,default=200)
    parser.add_argument("--fmax",type=float,default=0.01)
    parser.add_argument("--isif",type=int,default=3)
    parser.add_argument("--out",default="relaxed.xyz")
    parser.add_argument("--energy",default="energy.txt")
    args=parser.parse_args()

    atoms=read(args.structure)
    atoms.calc=CPUNEP(args.nep)
    if args.isif == 3:
        relax_structure(atoms,fmax=args.fmax,steps=args.steps,minimizer=args.opt,constant_cell=False,constant_volume=False,logfile="log.out")
    if args.isif == 2:
        relax_structure(atoms,fmax=args.fmax,steps=args.steps,minimizer=args.opt,constant_cell=True,constant_volume=True,logfile="log.out")

    energy=atoms.get_potential_energy()
    write(args.out,atoms)
    write_vasp('POSCAR_relaxed',atoms,direct=True,sort=True)
    np.savetxt(args.energy,[energy])

    print(f"Energy: {energy:.8f} eV")
    print(f"Saved: {args.out}")


if __name__=="__main__":
    main()