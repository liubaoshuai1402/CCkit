# CCkit 功能说明：
# 使用 ASE 构建指定晶面的表面模型，并生成不同终止面。
# 用于构建表面模型(ASE版本)
# 可以指定晶面、slab层数、真空层厚度
# 自动生成不同termination表面结构

from pathlib import Path
import argparse
import numpy as np

from ase.io import read, write
from ase.build import surface


def safe_name(s):
    return "".join(c if c.isalnum() or c in "-*." else "_" for c in str(s))

def main():

    parser = argparse.ArgumentParser(description="Generate surface slab models using ASE")
    parser.add_argument("--input", required=True, help="bulk structure file")
    parser.add_argument("--miller", nargs=3, type=int, required=True, help="Miller index")
    parser.add_argument("--layers", type=int, default=4, help="number of slab layers")
    parser.add_argument("--vacuum", type=float, default=15.0, help="vacuum thickness")
    parser.add_argument("--termination", type=int, default=5, help="number of terminations")
    parser.add_argument("--output", default=None)

    args = parser.parse_args()
    bulk = read(args.input)

    if args.output is None:
        args.output = (
            f"{Path(args.input).stem}_"
            f"{args.miller[0]}{args.miller[1]}{args.miller[2]}_"
            f"layer{args.layers}_vac{args.vacuum}"
        )

    outdir = Path(args.output)
    outdir.mkdir(exist_ok=True)

    slab = surface(bulk, args.miller, args.layers, vacuum=args.vacuum, periodic=True)
    slabs = [slab]

    print(f"Generated {len(slabs)} slabs")

    for i, s in enumerate(slabs):
        area = np.linalg.norm(np.cross(s.cell[0], s.cell[1]))

        name = (
            f"{safe_name(args.input)}_"
            f"{args.miller[0]}{args.miller[1]}{args.miller[2]}_"
            f"term{i}_"
            f"atoms{len(s)}_"
            f"area{area:.2f}.vasp"
        )

        outfile = outdir / name

        print(f"Writing {outfile} (atoms={len(s)}, area={area:.2f} Å²)")

        write(outfile, s, format="vasp", direct=True, sort=True)


if __name__ == "__main__":
    main()
