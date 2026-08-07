# CCkit 功能说明：
# 按照指定元素顺序重新排列 POSCAR 中的原子。
import argparse
from ase.io import read, write


def sort_atoms(atoms, element_order):
    order = {e: i for i, e in enumerate(element_order)}
    indices = sorted(
        range(len(atoms)), key=lambda i: order.get(atoms[i].symbol, len(order))
    )
    return atoms[indices]


def main():
    parser = argparse.ArgumentParser(description="Sort atoms in structure according to element order.")
    parser.add_argument("filename", help="Input structure file")
    parser.add_argument("-s", "--sort", nargs="+", required=True, help="Element order, e.g. Zr Fe O")
    parser.add_argument("-o", "--output", default="POSCAR_sorted", help="Output file name")
    args = parser.parse_args()

    atoms = read(args.filename)
    atoms_sorted = sort_atoms(atoms, args.sort)
    write(args.output, atoms_sorted, format="vasp", vasp5=True, direct=True)

    print("========== Sort POSCAR ==========")
    print(f"Input : {args.filename}")
    print(f"Order : {args.sort}")
    print(f"Output: {args.output}")
    print("=================================")


if __name__ == "__main__":
    main()
