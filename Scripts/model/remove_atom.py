import argparse
from ase.io import read,write


def remove_atoms(atoms,indices):
    return atoms[[i for i in range(len(atoms)) if i not in indices]]


def main():

    parser=argparse.ArgumentParser(description="Remove atoms from structure.")
    parser.add_argument("filename",help="Input structure file")
    parser.add_argument("indices",nargs="+",type=int,help="Atom indices to remove")
    parser.add_argument("-o","--output",default="POSCAR_removed")
    args=parser.parse_args()

    atoms=read(args.filename)

    n=len(atoms)

    for i in args.indices:
        if i<0 or i>=n:
            raise ValueError(f"Atom index {i} out of range.")

    new_atoms=remove_atoms(atoms,args.indices)
    output=f"{args.output}_{'_'.join(map(str,args.indices))}"
    write(
        output,
        new_atoms,
        format="vasp",
        vasp5=True,
        direct=True,
        sort=False
    )

    print("========== Remove Atoms ==========")
    print(f"Input : {args.filename}")
    print(f"Remove atoms : {args.indices}")
    print("==================================")


if __name__=="__main__":
    main()