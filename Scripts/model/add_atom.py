# CCkit 功能说明：
# 使用指定坐标或几何关系向结构中添加单个原子。
"""Add one atom by position, geometric center, or along an M-O line.

Read one structure and write it with a geometry-based filename suffix.
"""

import argparse
from itertools import combinations, product
from pathlib import Path

from ase import Atom, Atoms
from ase.geometry import wrap_positions
from ase.io import read, write
from ase.neighborlist import neighbor_list
import numpy as np


def calc_centroid(group: Atoms) -> np.ndarray:
    """Return the Cartesian centroid of a group in Angstrom.

    Use the input cell and PBC, including non-orthogonal cells. Consider tied
    nearest images to find a group whose pairwise distances are all minimal.
    Compare distances within 1e-8 Angstrom and wrap the resulting centroid.
    Raise ValueError when no such image combination exists.
    """
    if not group.pbc.any():
        return group.positions.mean(axis=0)

    tolerance = 1e-8
    minimum_distances = group.get_all_distances(mic=True)
    # Fix atom A and collect every nearest image of the other atoms.
    # ASE's neighbor search handles skew cells and arbitrary lattice shifts.
    first, second, distances, vectors = neighbor_list(
        "ijdD", group, cutoff=minimum_distances[0].max() + tolerance,
    )
    nearest_images = []
    for index in range(1, len(group)):
        from_anchor = (first == 0) & (second == index)
        is_nearest = np.abs(distances - minimum_distances[0, index]) <= tolerance
        nearest_images.append(vectors[from_anchor & is_nearest])

    # The distances to A are already minimal. Check the other pairs together.
    remaining_pairs = tuple(combinations(range(1, len(group)), 2))
    for images in product(*nearest_images):
        relative_positions = np.vstack(([0.0, 0.0, 0.0], *images))
        if all(
            abs(
                np.linalg.norm(relative_positions[j] - relative_positions[i])
                - minimum_distances[i, j]
            ) <= tolerance
            for i, j in remaining_pairs
        ):
            centroid = group.positions[0] + relative_positions.mean(axis=0)
            return wrap_positions([centroid], group.cell, pbc=group.pbc, eps=0.0)[0]

    raise ValueError(
        "No periodic image combination makes all pairwise distances minimal. "
        "Choose atoms forming a local group."
    )


def calc_position(mode: str, args: argparse.Namespace, atoms: Atoms) -> np.ndarray:
    """Return the added atom's Cartesian position in Angstrom.

    Tricenter, quadcenter and pentacenter use mutually nearest periodic images.
    Center, OH and rOH use the Cartesian coordinates as stored in the input.
    """
    if mode == "position":
        return np.array(args.position)

    elif mode == "center":
        posA=atoms[args.atomA].position
        posB=atoms[args.atomB].position
        return (posA+posB)/2

    elif mode in ("tricenter", "quadcenter", "pentacenter"):
        indices = [args.atomA, args.atomB, args.atomC]
        required_options = "--atomA, --atomB, --atomC"
        if mode in ("quadcenter", "pentacenter"):
            indices.append(args.atomD)
            required_options += ", --atomD"
        if mode == "pentacenter":
            indices.append(args.atomE)
            required_options += ", --atomE"
        if any(index is None for index in indices):
            raise ValueError(f"{mode} mode requires {required_options}")
        if any(index < 0 or index >= len(atoms) for index in indices):
            raise ValueError(f"{mode} atom indices must be in [0, {len(atoms)})")
        if len(set(indices)) != len(indices):
            raise ValueError(f"{mode} mode requires {len(indices)} distinct atom indices")
        return calc_centroid(atoms[indices])

    elif mode in ("OH", "rOH"):
        if args.O is None or args.M is None:
            raise ValueError(f"{mode} mode requires --O and --M")
        if mode == "rOH":
            if not (0 <= args.O < len(atoms) and 0 <= args.M < len(atoms)):
                raise ValueError(f"rOH atom indices must be in [0, {len(atoms)})")
            if not np.isfinite(args.distance) or args.distance <= 0:
                raise ValueError("rOH mode requires a finite, positive --distance")

        oxygen = atoms[args.O].position
        metal = atoms[args.M].position
        direction = metal - oxygen if mode == "rOH" else oxygen - metal
        length = np.linalg.norm(direction)
        if not np.isfinite(length) or length == 0:
            raise ValueError(f"{mode} mode requires a finite, nonzero O-M vector")
        return oxygen + direction / length * args.distance

    else:
        raise ValueError(f"Unknown mode: {mode}")


def add_atom(atoms, element, position):
    new_atoms = atoms.copy()
    new_atoms.append(Atom(element, position=position))
    return new_atoms


def main() -> None:
    parser = argparse.ArgumentParser(description="Add one atom with different modes.")
    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument(
        "--mode",
        choices=["position", "center", "tricenter", "quadcenter", "pentacenter", "OH", "rOH"],
        required=True,
        help=(
            "tricenter, quadcenter and pentacenter find the centroid of three, four or five "
            "mutually nearest periodic images. "
            "OH places from O along M-to-O and rOH places from O toward M."
        ),
    )
    parser.add_argument("--element", type=str, default="H", help="added atom element")

    # position mode
    parser.add_argument("--position", nargs=3, type=float, help="Cartesian position x y z")
    # Geometric center modes
    parser.add_argument("--atomA", type=int, help="atom A index (0-based)")
    parser.add_argument("--atomB", type=int, help="atom B index (0-based)")
    parser.add_argument(
        "--atomC", type=int, help="atom C index (0-based, tricenter, quadcenter or pentacenter)",
    )
    parser.add_argument("--atomD", type=int, help="atom D index (0-based, quadcenter or pentacenter)")
    parser.add_argument("--atomE", type=int, help="atom E index (0-based, pentacenter mode)")
    # OH / rOH modes
    parser.add_argument("--O", type=int, help="reference oxygen index (0-based)")
    parser.add_argument("--M", type=int, help="reference metal index (0-based, e.g. Zr)")
    parser.add_argument(
        "--distance", type=float, default=1.0,
        help="distance from O in Angstrom for OH or rOH (default: 1.0)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="output base name; bare names are placed beside the input (suffix is appended)",
    )

    args = parser.parse_args()

    atoms = read(args.input)
    try:
        pos = calc_position(args.mode, args, atoms)
    except (ValueError, IndexError) as error:
        parser.error(str(error))
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
    elif args.mode in ("rOH", "quadcenter", "pentacenter"):
        if args.mode == "rOH":
            suffix = f"rOH_{args.O}_{args.M}"
        else:
            suffix = f"{args.mode}_{args.atomA}_{args.atomB}_{args.atomC}_{args.atomD}"
            if args.mode == "pentacenter":
                suffix += f"_{args.atomE}"
        output_path = Path(f"{output_base}_{suffix}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write(output_path, atoms_new, format="vasp")
        print(f"Added 1 {args.element} atom. Output: {output_path.resolve()}")


if __name__ == "__main__":
    main()
