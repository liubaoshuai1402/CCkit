# CCkit 功能说明：
# 按照原子索引从结构中删除指定原子。
import argparse
import os
from ase.io import read, write

def remove_atoms(atoms, indices):
    return atoms[[i for i in range(len(atoms)) if i not in indices]]


def main():

    parser = argparse.ArgumentParser(description="Remove atoms from structure.")
    parser.add_argument("filename", help="Input structure file")
    parser.add_argument("indices", nargs="+", type=int, help="Atom indices to remove")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-s", "--sort", nargs="+", help="Sort elements order, e.g. Zr Fe O")
    args = parser.parse_args()

    atoms = read(args.filename)

    n = len(atoms)

    for i in args.indices:
        if i < 0 or i >= n:
            raise ValueError(f"Atom index {i} out of range.")

    new_atoms = remove_atoms(atoms, args.indices)

    # element sorting
    if args.sort:
        element_order = {e: i for i, e in enumerate(args.sort)}
        indices = sorted(range(len(new_atoms)),key=lambda i: element_order.get(new_atoms[i].symbol, len(element_order)))
        new_atoms = new_atoms[indices]

    output_base = args.output
    if output_base is None:
        input_dir = os.path.dirname(os.path.abspath(args.filename))
        output_base = os.path.join(input_dir, "POSCAR_removed")

    output = f"{output_base}_{'_'.join(map(str, args.indices))}"

    write(output, new_atoms, format="vasp", vasp5=True, direct=True, sort=False)

    print("========== Remove Atoms ==========")
    print(f"Input : {args.filename}")
    print(f"Remove atoms : {args.indices}")
    print("==================================")


if __name__ == "__main__":
    main()
