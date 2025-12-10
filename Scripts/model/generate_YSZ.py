import argparse
from ase.io import read,write
import random
from ase import Atoms

def generate_YSZ(prim, elementA, elementB, N1, elementC, N2):
    struct = prim.copy()
    A_indices = [i for i, atom in enumerate(struct) if atom.symbol == elementA]
    selected_indices = random.sample(A_indices, N1)
    for i in selected_indices:
        struct[i].symbol = elementB
    C_indices = [i for i, atom in enumerate(struct) if atom.symbol == elementC]
    delete_C_indices = random.sample(C_indices, N2)
    keep_indices = [i for i in range(len(struct)) if i not in delete_C_indices]
    struct_new = struct[keep_indices]
    return struct_new

def main():
    parser = argparse.ArgumentParser(description="Random YSZ type generator (conatin substitute and vacancy simultaneously).")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("elementA", type=str, help="Element to replace")
    parser.add_argument("elementB", type=str, help="Element replacing")
    parser.add_argument("N1", type=int, help="Number of A atoms replaced by B")
    parser.add_argument("elementC", type=str, help="Element to delete")
    parser.add_argument("M", type=int, help="Number of structures for each prim to generate")

    parser.add_argument("--N2", type=int, default=None, help="Number of vacancy of C atoms")
    parser.add_argument("--seed", type=int, default=1214, help="Random seed, default: 1214")
    parser.add_argument("-o", "--output", type=str, default="ysztype.xyz", help="Output file, default: ysztype.xyz")

    args = parser.parse_args()
    if args.N2 is None:
        args.N2 = args.N1 // 2

    # --- Load structure and seed---
    prims: list[Atoms] = read(args.input,':')
    random.seed(args.seed)

    # --- Generate all substituted structures ---
    output_structs = []
    for prim in prims:
        ysztype_structures: list[Atoms] = [generate_YSZ(prim, args.elementA, args.elementB, args.N1, args.elementC, args.N2) for _ in range(args.M)]
        output_structs.extend(ysztype_structures)

    # --- Write output ---
    write(args.output, output_structs)
    print(f"Generated {len(prims) * args.M} structures → {args.output}")

if __name__ == "__main__":
    main()
