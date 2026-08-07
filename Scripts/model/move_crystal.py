# CCkit 功能说明：
# 将指定原子移动到原点，同时整体平移晶体保持内部构型不变。
# 将指定原子移动到原点，同时整体平移晶体

import argparse
from ase.io import read, write


def move_atom_origin(input_file, index, output):

    atoms = read(input_file)

    # 获取目标原子坐标
    pos = atoms[index].position.copy()

    # 整体平移
    atoms.translate(-pos)

    # 保持周期边界
    atoms.wrap()

    write(output, atoms, format="vasp", direct=True, vasp5=True, sort=False)


def main():

    parser = argparse.ArgumentParser(description="Move selected atom to origin by translating whole structure")
    parser.add_argument("input", help="Input structure file")
    parser.add_argument("index", type=int, help="Atom index (ASE index starts from 0)")
    parser.add_argument("--output", default=None, help="Output structure file")
    args = parser.parse_args()

    if args.output is None:
        args.output = f"POSCAR_shifted_atom{args.index}"

    move_atom_origin(args.input, args.index, args.output)


if __name__ == "__main__":
    main()
