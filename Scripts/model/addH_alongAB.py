# CCkit 功能说明：
# 沿两个原子定义的方向添加氢原子。
from ase.io import read, write
import numpy as np
import argparse

def h_post(atomA_pos,atomB_pos):
    atomC_pos = atomB_pos + (atomB_pos - atomA_pos) / np.linalg.norm(atomB_pos - atomA_pos)
    return atomC_pos

def add_H(struct,atomA_indix,atomB_indix,atomC_type):
    struct_h = struct.copy()
    atomA = struct[atomA_indix]
    atomB = struct[atomB_indix]
    positionC = h_post(atomA.position, atomB.position)
    struct_h.append(Atom(atomC_type, position=positionC))
    return struct_h

def main():
    parser = argparse.ArgumentParser(description="add a atom along atomA → atomB,distant 1.0 to atomB.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("atomA",type=int,help="one atom in the line")
    parser.add_argument("atomB",type=int,help="one atom in the line")
    parser.add_argument("--type_atomC",type=str,default="H",help="type of added atom, default is H")
    parser.add_argument("--output",type=str,default="H_added.xyz",help="output file name, default is H_added.xyz")

    args = parser.parse_args()
    db = read(args.input)
    db_h = add_H(db,args.atomA,args.atomB,args.type_atomC)
    write(args.output, db_h)

if __name__ == "__main__":
    main()
