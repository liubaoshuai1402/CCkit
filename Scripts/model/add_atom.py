# CCkit 功能说明：
# 使用指定坐标或几何关系向结构中添加单个原子。
# This script is used to add a single atom to a structure using different methods.
#
# Three modes are available:
# 1. position:
#    Add an atom at a user-defined Cartesian coordinate.
#
# 2. center:
#    Add an atom at the midpoint between two specified atoms using their indices.
#
# 3. OH:
#    Add an H atom along the M-O bond direction.
#    The H atom is placed at a specified distance from the O atom.

from ase.io import read, write
from ase import Atom
import numpy as np
import argparse


def calc_position(mode, args, atoms):
    if mode == "position":
        return np.array(args.position)

    elif mode == "center":
        posA=atoms[args.atomA].position
        posB=atoms[args.atomB].position
        return (posA+posB)/2

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
    parser.add_argument("--mode",choices=["position", "center", "OH"],required=True,help="adding mode",)
    parser.add_argument("--element", type=str, default="H", help="added atom element")

    # position mode
    parser.add_argument("--position", nargs=3, type=float, help="Cartesian position x y z")
    # center mode
    parser.add_argument("--atomA", type=int, help="atom A index")
    parser.add_argument("--atomB", type=int, help="atom B index")
    #add a atom along M → O, distant 1.0 to O.
    parser.add_argument("--O", type=int, help="oxygen index")
    parser.add_argument("--M", type=int, help="metal index")
    parser.add_argument("--distance", type=float, default=1.0, help="distance to reference O atom")
    parser.add_argument("--output", type=str, default="POSCAR")

    args = parser.parse_args()

    atoms = read(args.input)
    pos = calc_position(args.mode, args, atoms)
    atoms_new = add_atom(atoms, args.element, pos)

    if args.mode == "position":
        pos = list(args.position)
        write(f"{args.output}_{pos[0]:.3f}_{pos[1]:.3f}_{pos[2]:.3f}", atoms_new)
    elif args.mode == "center":
        write(f"{args.output}_center_{args.atomA}_{args.atomB}", atoms_new)
    elif args.mode == "OH":
        write(f"{args.output}_OH_{args.O}_{args.M}", atoms_new)


if __name__ == "__main__":
    main()
