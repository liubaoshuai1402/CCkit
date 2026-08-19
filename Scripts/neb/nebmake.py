# CCkit 功能说明：
# 根据初态和终态结构插值生成 NEB 图片目录，并统计初末结构对应原子的距离差总和。
import os
import argparse
import numpy as np
from pymatgen.core import Structure


def compute_total_displacement(start: Structure, end: Structure) -> tuple[np.ndarray, float]:
    """Return per-atom minimum-image distances between corresponding sites and their sum."""
    delta_frac = end.frac_coords - start.frac_coords
    delta_frac[:, start.pbc] -= np.round(delta_frac[:, start.pbc])
    delta_cart = delta_frac @ start.lattice.matrix
    per_atom = np.linalg.norm(delta_cart, axis=1)
    return per_atom, float(per_atom.sum())


def main():
    parser=argparse.ArgumentParser(description="Generate NEB images by pymatgen interpolation.")
    parser.add_argument("initial",help="Initial POSCAR")
    parser.add_argument("final",help="Final POSCAR")
    parser.add_argument("-n","--nimages",type=int,default=5)
    parser.add_argument("-t","--tol",type=float,default=0.5,help="Autosort tolerance (default: 0.5 Angstrom)")
    args=parser.parse_args()

    initial=Structure.from_file(args.initial)
    final=Structure.from_file(args.final)

    if len(initial)!=len(final):
        raise ValueError("Atom numbers are inconsistent.")
    if initial.species!=final.species:
        raise ValueError("Atom ordering is inconsistent.")

    images=initial.interpolate(final,nimages=args.nimages+1,interpolate_lattices=False,autosort_tol=args.tol,pbc=True)

    # 用插值生成的端点结构：autosort 后 images[-1] 与 images[0] 的原子顺序一致，按下标即对应原子。
    _, total_distance = compute_total_displacement(images[0], images[-1])

    for i,img in enumerate(images):
        path=f"{i:02d}"
        os.makedirs(path,exist_ok=True)
        img.to(filename=f"{path}/POSCAR",fmt="poscar")

    print("========== NEB path interpolated by pymatgen==========")
    print(f"Initial : {args.initial}")
    print(f"Final   : {args.final}")
    print(f"Images  : {len(images)-1}")
    print(f"autosort tolerance : {args.tol} Angstrom")
    print(f"Total distance difference (initial -> final): {total_distance:.3f} Angstrom")
    print("=========================")

if __name__=="__main__":
    main()
