# CCkit 功能说明：
# 按照原子索引将指定原子替换为目标元素。
import argparse
from ase.io import read, write

def replace_atoms(atoms, indices, element):
    new_atoms = atoms.copy()
    for i in indices:
        new_atoms[i].symbol = element
    return new_atoms


def main():
    parser = argparse.ArgumentParser(description="Replace atoms in structure.")
    parser.add_argument("filename", help="Input structure file")
    parser.add_argument("indices", nargs="+", type=int, help="Atom indices to replace")
    parser.add_argument("-e", "--element", required=True, help="New element symbol")
    parser.add_argument("-o", "--output", default="POSCAR_replaced")
    parser.add_argument("-s", "--sort", nargs="+", help="Sort elements order, e.g. Zr Fe O")
    args = parser.parse_args()

    atoms = read(args.filename)

    n = len(atoms)

    for i in args.indices:
        if i < 0 or i >= n:
            raise ValueError(f"Atom index {i} out of range.")

    new_atoms = replace_atoms(atoms, args.indices, args.element)
    # element sorting
    if args.sort:
        element_order = {e: i for i, e in enumerate(args.sort)}
        indices = sorted(range(len(new_atoms)),key=lambda i: element_order.get(new_atoms[i].symbol, len(element_order)))
        new_atoms = new_atoms[indices]

    output = f"{args.output}_{args.element}_{'_'.join(map(str, args.indices))}"

    write(output, new_atoms, format="vasp", vasp5=True, direct=True)

    print("========== Replace Atoms ==========")
    print(f"Input : {args.filename}")
    print(f"Replace atoms : {args.indices}")
    print(f"New element : {args.element}")
    print("===================================")


if __name__ == "__main__":
    main()
