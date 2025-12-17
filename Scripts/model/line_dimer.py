#add a dimer along a line defined by two atoms
import numpy as np
from ase.io import read, write
from ase import Atom, Atoms
import argparse

def line_sphere_intersections(r1, r2, R):
    r1 = np.asarray(r1, dtype=float)
    r2 = np.asarray(r2, dtype=float)

    # 球心（中点）
    center = 0.5 * (r1 + r2)

    # 方向单位向量
    direction = r2 - r1
    direction /= np.linalg.norm(direction)

    # 两个交点
    p1 = center + R * direction
    p2 = center - R * direction

    return p1, p2

def add_dimer(input: Atoms,atom1,atom2,type_dimer,r):
    atom1 = input[atom1]
    atom2 = input[atom2]
    dimer = line_sphere_intersections(atom1.position, atom2.position, r)
    input.append(Atom(type_dimer, position=dimer[0]))
    input.append(Atom(type_dimer, position=dimer[1]))

def main():
    parser = argparse.ArgumentParser(description="add a dimer at center of a line defined by two atoms.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("atom1",type=int,help="one atom in the line")
    parser.add_argument("atom2",type=int,help="one atom in the line")
    parser.add_argument("--type_dimer",type=str,default="H",help="type of the dimer atom, default is H")
    parser.add_argument("--r",type=float,default=0.37,help="radius of the dimer, default is 0.37")
    parser.add_argument("--output",type=str,default="dimer_added.xyz",help="output file name, default is dimer_added.xyz")

    args = parser.parse_args()

    db = read(args.input)
    add_dimer(db, args.atom1, args.atom2, args.type_dimer, args.r)
    write(args.output, db)

if __name__ == "__main__":
    main()