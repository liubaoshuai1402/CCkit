# CCkit 功能说明：
# 将 XYZ 结构集合准备为一系列 VASP 单点计算目录。
import os
import argparse
from ase.io import read
from ase.io.vasp import write_vasp
import shutil

def main():
    parser=argparse.ArgumentParser(description="Convert xyz structures to VASP POSCAR files")
    parser.add_argument("-i",default="train.xyz",help="Input xyz file")
    parser.add_argument("--out",default="singlepoint",help="Output directory")
    args=parser.parse_args()

    db=read(args.i,":")

    os.makedirs(args.out,exist_ok=True)

    for number,at in enumerate(db):
        number_path=os.path.join(args.out,str(number))
        os.makedirs(number_path,exist_ok=True)
        if at.has("momenta"):
            del at.arrays["momenta"]
        POSCAR_path=os.path.join(number_path,"POSCAR")
        write_vasp(POSCAR_path,at,direct=True,sort=False)

    print(f"Converted {len(db)} structures to {args.out}")
    shutil.make_archive(args.out,"zip",args.out)
    print(f"Compressed {args.out}.zip")

if __name__=="__main__":
    main()
