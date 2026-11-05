# CCkit 功能说明：
# 使用指定坐标或几何关系向结构中添加单个原子。
"""Add one atom by position, midpoint, triangle centroid, or M-O direction.

Read one structure and write it with a geometry-based filename suffix.
"""

import argparse
from pathlib import Path

from ase import Atom, Atoms
from ase.geometry import wrap_positions
from ase.io import read, write
from ase.neighborlist import neighbor_list
import numpy as np


def calc_tricenter(triangle: Atoms) -> np.ndarray:
    """Return the wrapped centroid of three atoms with shortest pairwise edges.

    Use the input cell and PBC, including non-orthogonal cells. Enumerate tied
    nearest images so all three edges belong to one consistent triangle.
    Distances are compared with a tolerance of 1e-8 Angstrom. Raise ValueError
    when no image combination realizes all three minimum-image distances.
    """
    if len(triangle) != 3:
        raise ValueError("tricenter mode requires exactly three atoms")
    if not triangle.pbc.any():
        return triangle.positions.mean(axis=0)

    tolerance = 1e-8
    minimum_distances = triangle.get_all_distances(mic=True)
    # Fix A and collect every nearest image of B and C, including ties.
    # ASE's neighbor search handles skew cells and arbitrary lattice shifts.
    first, second, distances, vectors = neighbor_list(
        "ijdD", triangle, cutoff=minimum_distances[0].max() + tolerance,
    )
    nearest_b = vectors[
        (first == 0) & (second == 1)
        & (np.abs(distances - minimum_distances[0, 1]) <= tolerance)
    ]
    nearest_c = vectors[
        (first == 0) & (second == 2)
        & (np.abs(distances - minimum_distances[0, 2]) <= tolerance)
    ]
    for vector_b in nearest_b:
        for vector_c in nearest_c:
            # Nearest A-B and A-C images need not give a nearest B-C edge.
            distance_bc = np.linalg.norm(vector_c - vector_b)
            if abs(distance_bc - minimum_distances[1, 2]) <= tolerance:
                centroid = triangle.positions[0] + (vector_b + vector_c) / 3.0
                return wrap_positions(
                    [centroid], triangle.cell, pbc=triangle.pbc, eps=0.0,
                )[0]

    raise ValueError(
        "tricenter: no periodic image combination makes all three pairwise "
        "distances minimal; choose three atoms forming a local triangle"
    )


def calc_position(mode: str, args: argparse.Namespace, atoms: Atoms) -> np.ndarray:
    """Return the added atom's Cartesian position in Angstrom.

    Tricenter uses mutually nearest periodic images; center uses stored coordinates.
    """
    if mode == "position":
        return np.array(args.position)

    elif mode == "center":
        posA=atoms[args.atomA].position
        posB=atoms[args.atomB].position
        return (posA+posB)/2

    elif mode == "tricenter":
        indices = [args.atomA, args.atomB, args.atomC]
        if any(index is None for index in indices):
            raise ValueError("tricenter mode requires --atomA, --atomB, and --atomC")
        if any(index < 0 or index >= len(atoms) for index in indices):
            raise ValueError(f"tricenter atom indices must be in [0, {len(atoms)})")
        if len(set(indices)) != 3:
            raise ValueError("tricenter mode requires three distinct atom indices")
        return calc_tricenter(atoms[indices])

    elif mode == "OH":
        O = atoms[args.O].position
        M = atoms[args.M].position
        vec = O - M
        return O + vec / np.linalg.norm(vec) * args.distance

    else:
        raise ValueError(f"Unknown mode: {mode}")


def add_atom(atoms, element, position):
    new_atoms = atoms.copy()
    new_atoms.append(Atom(element, position=position))
    return new_atoms


def main():
    parser = argparse.ArgumentParser(description="Add one atom with different modes.")
    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument(
        "--mode", choices=["position", "center", "tricenter", "OH"],
        required=True,
        help="adding mode (tricenter: centroid of three mutually nearest periodic images)",
    )
    parser.add_argument("--element", type=str, default="H", help="added atom element")

    # position mode
    parser.add_argument("--position", nargs=3, type=float, help="Cartesian position x y z")
    # center / tricenter modes
    parser.add_argument("--atomA", type=int, help="atom A index (0-based)")
    parser.add_argument("--atomB", type=int, help="atom B index (0-based)")
    parser.add_argument("--atomC", type=int, help="atom C index (0-based, tricenter mode)")
    #add a atom along M → O, distant 1.0 to O.
    parser.add_argument("--O", type=int, help="oxygen index")
    parser.add_argument("--M", type=int, help="metal index")
    parser.add_argument("--distance", type=float, default=1.0, help="distance to reference O atom")
    parser.add_argument(
        "--output", type=str, default=None,
        help="output base name; bare names are placed beside the input (suffix is appended)",
    )

    args = parser.parse_args()

    atoms = read(args.input)
    pos = calc_position(args.mode, args, atoms)
    atoms_new = add_atom(atoms, args.element, pos)

    input_dir = Path(args.input).resolve().parent
    if args.output is None:
        output_base = input_dir / "POSCAR"
    else:
        output_base = Path(args.output)
        if not output_base.is_absolute() and not any(
            separator in args.output for separator in ("/", "\\")
        ):
            output_base = input_dir / output_base

    if args.mode == "position":
        pos = list(args.position)
        write(f"{output_base}_{pos[0]:.3f}_{pos[1]:.3f}_{pos[2]:.3f}", atoms_new)
    elif args.mode == "center":
        write(f"{output_base}_center_{args.atomA}_{args.atomB}", atoms_new)
    elif args.mode == "tricenter":
        write(f"{output_base}_tricenter_{args.atomA}_{args.atomB}_{args.atomC}", atoms_new)
    elif args.mode == "OH":
        write(f"{output_base}_OH_{args.O}_{args.M}", atoms_new)


if __name__ == "__main__":
    main()
