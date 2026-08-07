# CCkit 功能说明：
# 按照给定的三个方向倍数生成晶体超胞。
from ase.io import read, write
from ase.build import make_supercell
import argparse

def supercell_builder(prim,scale_x,scale_y,scale_z):
    P = [[scale_x, 0, 0],[0, scale_y, 0],[0, 0, scale_z]]
    supercell = make_supercell(prim, P, order="atom-major")
    return supercell



def main():
    parser = argparse.ArgumentParser(description="Generate supercell, please give only one structure.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("scale_x",type=int,help="scale factors of a axis for supercell")
    parser.add_argument("scale_y",type=int,help="scale factors of b axis for supercell")
    parser.add_argument("scale_z",type=int,help="scale factors of c axis for supercell")
    parser.add_argument("--output",type=str,default = "supercell.xyz",help="output file name, default is supercell.xyz")

    args = parser.parse_args()

    prim = read(args.input)
    prim_supercell = supercell_builder(prim,args.scale_x,args.scale_y,args.scale_z)
    write(args.output, prim_supercell)


if __name__ == "__main__":
    main()
