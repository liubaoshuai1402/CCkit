# CCkit 功能说明：
# 根据初态和终态结构插值生成 NEB 图片目录。
import os
import argparse
from pymatgen.core import Structure

def main():
    parser=argparse.ArgumentParser(description="Generate NEB images by pymatgen interpolation.")
    parser.add_argument("initial",help="Initial POSCAR")
    parser.add_argument("final",help="Final POSCAR")
    parser.add_argument("-n","--nimages",type=int,default=5)
    parser.add_argument("-t","--tol",type=float,default=0.5,help="Autosort tolerance (default: 0.5 Å)")
    args=parser.parse_args()

    initial=Structure.from_file(args.initial)
    final=Structure.from_file(args.final)

    if len(initial)!=len(final):
        raise ValueError("Atom numbers are inconsistent.")
    if initial.species!=final.species:
        raise ValueError("Atom ordering is inconsistent.")

    images=initial.interpolate(final,nimages=args.nimages+1,interpolate_lattices=False,autosort_tol=args.tol,pbc=True)

    for i,img in enumerate(images):
        path=f"{i:02d}"
        os.makedirs(path,exist_ok=True)
        img.to(filename=f"{path}/POSCAR",fmt="poscar")

    print("========== NEB path interpolated by pymatgen==========")
    print(f"Initial : {args.initial}")
    print(f"Final   : {args.final}")
    print(f"Images  : {len(images)-1}")
    print(f"autosort tolerance : {args.tol} Å")
    print("=========================")

if __name__=="__main__":
    main()
