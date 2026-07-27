
import numpy as np
import matplotlib.pyplot as plt
from ase.io import read,write
from calorine.calculators import CPUNEP
import os
import argparse

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--neb",default=".",help="NEB directory")
    parser.add_argument("--nep",default="nep.txt",help="NEP potential file")
    parser.add_argument("--out",default="EnergyBarrierDFTvsNEP",help="Output file name")
    args=parser.parse_args()

    calc=CPUNEP(args.nep)
    #确定所有00、01等文件夹
    folders=sorted([f for f in os.listdir(args.neb) if f.isdigit()],key=int)

    img=[]
    dft=[]
    nep=[]
    nebsample = []

    for f in folders:
        path=os.path.join(args.neb,f)
        outcar=os.path.join(path,"OUTCAR")
        if not os.path.exists(outcar):
            outcar+=".gz"
        atoms=read(outcar)
        dft.append(atoms.get_potential_energy())

        structure="CONTCAR" if os.path.exists(os.path.join(path,"CONTCAR")) else "POSCAR"
        atoms=read(os.path.join(path,structure))
        nebsample.append(atoms.copy())
        atoms.calc=calc
        nep.append(atoms.get_potential_energy())

        img.append(int(f))
    nep=np.array(nep)-nep[0]
    dft=np.array(dft)-dft[0]

    img=np.array(img)
    for atoms in nebsample:
        if "momenta" in atoms.arrays:
            del atoms.arrays["momenta"]
    writefile = os.path.join(args.neb, "nebsample.xyz")
    write(writefile, nebsample)

    print(f"DFT barrier: {dft.max():.4f} eV")
    print(f"NEP barrier: {nep.max():.4f} eV")

    np.savetxt(args.out+".txt",
               np.column_stack([img,dft,nep]),
               header="Image DFT(eV) NEP(eV)",
               fmt=["%d","%.6f","%.6f"])

    plt.figure(figsize=(5,4))
    plt.plot(img,dft,"o-",label="DFT")
    plt.plot(img,nep,"s--",label="NEP")
    plt.xlabel("Reaction coordinate")
    plt.ylabel("Relative energy (eV)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(args.out+".png",dpi=600)

if __name__=="__main__":
    main()

