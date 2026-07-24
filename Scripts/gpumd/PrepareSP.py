import os
import argparse
from ase.io import read
from ase.io.vasp import write_vasp

def main():
    parser=argparse.ArgumentParser(description="Convert xyz structures to VASP POSCAR files")
    parser.add_argument("--xyz",default="train.xyz",help="Input xyz file")
    parser.add_argument("--out",default="singlepoint",help="Output directory")
    args=parser.parse_args()

    db=read(args.xyz,":")

    os.makedirs(args.out,exist_ok=True)

    for number,at in enumerate(db):
        number_path=os.path.join(args.out,str(number))
        os.makedirs(number_path,exist_ok=True)

        POSCAR_path=os.path.join(number_path,"POSCAR")
        write_vasp(POSCAR_path,at,direct=True,sort=True)

    print(f"Converted {len(db)} structures to {args.out}")

if __name__=="__main__":
    main()