# CCkit 功能说明：
# 使用 pymatgen 构建指定晶面的表面模型，并生成不同终止面。
# 用于构建表面模型
# 可以指定晶面、slab厚度、真空层厚度
# 自动生成不同termination表面结构

from pathlib import Path
import argparse
from pymatgen.core import Structure
from pymatgen.core.surface import SlabGenerator
from pymatgen.io.vasp import Poscar


def safe_name(s):
    return "".join(c if c.isalnum() or c in "-*." else "_" for c in str(s))


def main():

    parser = argparse.ArgumentParser(description="Generate surface slab models")
    parser.add_argument("--input", required=True, help="bulk structure file")
    parser.add_argument("--miller", nargs=3, type=int, required=True, help="Miller index, e.g. 1 0 0")
    parser.add_argument("--thickness", type=float, default=5.0, help="slab thickness in Angstrom")
    parser.add_argument("--vacuum", type=float, default=15.0, help="vacuum thickness in Angstrom")
    parser.add_argument("--output", default=None, help="output directory")
    parser.add_argument("--center", action="store_true", help="center slab in vacuum")

    args = parser.parse_args()

    bulk = Structure.from_file(args.input)

    if args.output is None:
        args.output = (
            f"{Path(args.input).stem}_"
            f"{args.miller[0]}{args.miller[1]}{args.miller[2]}_"
            f"thick{args.thickness}_vac{args.vacuum}"
        )

    outdir = Path(args.output)
    outdir.mkdir(exist_ok=True)

    slabgen = SlabGenerator(
        initial_structure=bulk,
        miller_index=tuple(args.miller),
        min_slab_size=args.thickness,
        min_vacuum_size=args.vacuum,
        center_slab=args.center,
        in_unit_planes=False,
        lll_reduce=False,
        max_normal_search=1,
        primitive=False,
    )

    slabs = slabgen.get_slabs(bonds = {("Zr", "O"): 3},max_broken_bonds=100,symmetrize=False)

    print(f"Generated {len(slabs)} slabs\n")

    for i, slab in enumerate(slabs):
        area = slab.surface_area

        name = (
            f"{safe_name(args.input)}_"
            f"{args.miller[0]}{args.miller[1]}{args.miller[2]}_"
            f"term{i}_"
            f"atoms{len(slab)}_"
            f"area{area:.2f}.vasp"
        )

        outfile = outdir / name

        print(f"Writing {outfile} (atoms={len(slab)}, area={area:.2f} Å²)")

        Poscar(slab).write_file(outfile)


if __name__ == "__main__":
    main()
