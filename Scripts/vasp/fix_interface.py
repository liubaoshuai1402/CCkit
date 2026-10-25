# CCkit 功能说明：
# 根据分数坐标 z 范围固定界面结构中的原子。
# 将 z 属于 [0, z1) 或 [z2, 1) 的原子固定，中间 z1 <= z < z2 的原子可以自由移动。
import argparse
import os
from ase.io import read, write
from ase.constraints import FixAtoms


def fix_interface_atoms(input_file, output_file, z1, z2):
    atoms = read(input_file)

    frac = atoms.get_scaled_positions()

    fixed_indices = [
        i for i, z in enumerate(frac[:, 2]) if z < z1 or z >= z2
    ]

    atoms.set_constraint(FixAtoms(indices=fixed_indices))

    atoms.info["vasp_sort"] = False

    write(output_file, atoms, format="vasp", direct=True, sort=False, vasp5=True)


def main():
    parser = argparse.ArgumentParser(description="Fix atoms by fractional z range (fix two interfaces)")
    parser.add_argument("input", help="input POSCAR")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--z1", type=float, required=True,
                        help="fractional z lower bound of the movable middle region")
    parser.add_argument("--z2", type=float, required=True,
                        help="fractional z upper bound of the movable middle region")
    args = parser.parse_args()

    if not (0.0 <= args.z1 < args.z2 <= 1.0):
        parser.error("require 0.0 <= z1 < z2 <= 1.0")

    output = args.output
    if output is None:
        input_dir = os.path.dirname(os.path.abspath(args.input))
        output = os.path.join(input_dir, "POSCAR_fixed")
    elif not os.path.dirname(args.output):
        # bare filename: write next to the input file, not the cwd
        input_dir = os.path.dirname(os.path.abspath(args.input))
        output = os.path.join(input_dir, args.output)
    else:
        output = args.output

    fix_interface_atoms(args.input, output, args.z1, args.z2)


if __name__ == "__main__":
    main()
