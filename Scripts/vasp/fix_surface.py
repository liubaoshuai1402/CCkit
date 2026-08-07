# CCkit 功能说明：
# 根据分数坐标 z 范围固定表面结构中的原子。
import argparse
from ase.io import read, write
from ase.constraints import FixAtoms

def fix_atoms_by_zfrac(input_file, output_file, zmin, zmax):
    atoms = read(input_file)

    frac = atoms.get_scaled_positions()

    flags = []
    for z in frac[:, 2]:
        if zmin <= z < zmax:
            flags.append([False, False, False])
        else:
            flags.append([True, True, True])

    atoms.set_constraint(
        FixAtoms(indices=[i for i, f in enumerate(flags) if f == [False, False, False]])
    )

    atoms.info["vasp_sort"] = False

    write(output_file, atoms, format="vasp", direct=True, sort=False, vasp5=True)





def main():
    parser = argparse.ArgumentParser(description="Fix atoms by fractional z range")
    parser.add_argument("input", help="input POSCAR")
    parser.add_argument("-o", "--output", default="POSCAR_fixed")
    parser.add_argument("--zrange", nargs=2, type=float, required=True, metavar=("ZMIN", "ZMAX"))
    args = parser.parse_args()

    fix_atoms_by_zfrac(args.input, args.output, args.zrange[0], args.zrange[1])


if __name__ == "__main__":
    main()
