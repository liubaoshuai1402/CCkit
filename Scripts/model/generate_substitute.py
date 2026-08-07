# CCkit 功能说明：
# 随机将结构中的指定元素替换为另一种元素，生成替位结构。
import argparse
import random
from ase.io import read, write

def load_structure(filename):
    """Read structure file into ASE Atoms."""
    return read(filename)

def substitute_atoms(prim, elementA, elementB, N):
    """Generate one substituted structure."""
    struct = prim.copy()

    # Locate atoms of type A
    A_indices = [i for i, atom in enumerate(struct) if atom.symbol == elementA]

    if len(A_indices) < N:
        raise ValueError(
            f"Only {len(A_indices)} atoms of type {elementA} found, but N={N} required."
        )

    # Select N atoms to replace
    selected = random.sample(A_indices, N)

    # Replace them
    for idx in selected:
        struct[idx].symbol = elementB

    return struct


def main():
    parser = argparse.ArgumentParser(description="Random atomic substitution generator.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("elementA", type=str, help="Element to replace")
    parser.add_argument("elementB", type=str, help="Element replacing")
    parser.add_argument("N", type=int, help="Number of A atoms replaced by B")
    parser.add_argument("M", type=int, help="Number of structures to generate")

    parser.add_argument("--seed", type=int, default=1214, help="Random seed")
    parser.add_argument("-o", "--output", type=str, default="substituted.xyz",
                        help="Output file")

    args = parser.parse_args()

    # --- Load structure ---
    prim = load_structure(args.input)
    random.seed(args.seed)

    # --- Generate all substituted structures ---
    substituted = [substitute_atoms(prim, args.elementA, args.elementB, args.N) for _ in range(args.M)]

    # --- Write output ---
    write(args.output, substituted)
    print(f"Generated {args.M} structures → {args.output}")


if __name__ == "__main__":
    main()
