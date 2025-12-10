import argparse
import random
from ase.io import read, write

def load_structure(filename):
    """Read structure file into ASE Atoms."""
    return read(filename)

def vacancy_atoms(prim, elementA, N):
    """Generate one substituted structure using a given seed."""
    struct = prim.copy()

    # Locate atoms of type A
    A_indices = [i for i, atom in enumerate(struct) if atom.symbol == elementA]

    if len(A_indices) < N:
        raise ValueError(
            f"Only {len(A_indices)} atoms of type {elementA} found, but N={N} required."
        )

    # Select N atoms to delete
    delete_A_indices = random.sample(A_indices, N)
    keep_indices = [i for i in range(len(struct)) if i not in delete_A_indices]
    struct_vacancy = struct[keep_indices]

    return struct_vacancy



def main():
    parser = argparse.ArgumentParser(description="Random atomic vacancy generator.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("elementA", type=str, help="Element to delete")
    parser.add_argument("N", type=int, help="Number of vacancies of elementA")
    parser.add_argument("M", type=int, help="Number of structures to generate")

    parser.add_argument("--seed", type=int, default=1214,
                        help="Main random seed (default = 1214)")
    parser.add_argument("-o", "--output", type=str, default="vacancy_structures.xyz",
                        help="Output file name")

    args = parser.parse_args()
    #load atoms and seed
    prim = load_structure(args.input)
    random.seed(args.seed)
    #generate M structures with vacancy
    vacancy_structures = [vacancy_atoms(prim, args.elementA, args.N, seed) for _ in range(M)]

    write(args.output,vacancy_structures)


if __name__ == "__main__":
    main()