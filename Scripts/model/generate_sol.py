from pymatgen.core import Structure
from pymatgen.transformations.advanced_transformations import (
    EnumerateStructureTransformation,
)
from pymatgen.io.vasp import Poscar
from collections import Counter
import argparse
import os


def main():

    parser = argparse.ArgumentParser(
        description="Enumerate substitutional doping structures using enumlib"
    )

    parser.add_argument("poscar", help="input POSCAR")
    parser.add_argument("dopant", help="dopant element, e.g. Nb,Y,Fe")
    parser.add_argument("number", type=int, help="number of dopant atoms")

    parser.add_argument("--host", default="Zr", help="host element to replace")

    parser.add_argument("--max_structures", type=int, default=10000)

    args = parser.parse_args()

    structure = Structure.from_file(args.poscar)
    original_lattice = structure.lattice

    host_sites = [i for i, s in enumerate(structure.species) if s.symbol == args.host]

    nhost = len(host_sites)

    if args.number > nhost:
        raise ValueError("dopant number larger than host sites")

    fraction = args.number / nhost

    print("Original:")
    print(structure.composition)

    print(f"{args.host}->{args.dopant}: {args.number}/{nhost}")

    # 混合占位
    for i in host_sites:
        structure.replace(i, {args.host: 1 - fraction, args.dopant: fraction})

    print("Disordered:")
    print(structure.composition)

    enum = EnumerateStructureTransformation(
        min_cell_size=1, max_cell_size=1, symm_prec=0.01, refine_structure=False
    )

    structures = enum.apply_transformation(
        structure, return_ranked_list=args.max_structures
    )
    print("Unique structures:", len(structures))

    # 总文件夹
    output_dir = f"{args.dopant}{args.number}_structures"

    os.makedirs(output_dir, exist_ok=True)

    # 每个结构单独文件夹
    for i, item in enumerate(structures):
        #enbale initial a-b-c axis
        old = item["structure"]
        s=Structure(lattice=original_lattice,species=old.species,coords=old.cart_coords,coords_are_cartesian=True)

        count = Counter([x.symbol for x in s.species])

        print(i, count)

        folder = os.path.join(output_dir, f"{args.dopant}{args.number}_{i:03d}")

        os.makedirs(folder, exist_ok=True)

        Poscar(s).write_file(os.path.join(folder, "POSCAR"))


if __name__ == "__main__":
    main()
