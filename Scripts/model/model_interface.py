# CCkit 功能说明：
# 根据晶面、层厚和界面间距构建相干界面模型。
#用于构建界面模型
#可以指定晶面，厚度，界面间距离
from pathlib import Path
import argparse
import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.interfaces.coherent_interfaces import CoherentInterfaceBuilder
from pymatgen.analysis.interfaces.zsl import ZSLGenerator
from pymatgen.io.vasp import Poscar


def calc_zsl_misfit(match):
    film = np.array(match.film_sl_vectors)
    sub = np.array(match.substrate_sl_vectors)
    lf = np.linalg.norm(film, axis=1)
    ls = np.linalg.norm(sub, axis=1)
    return np.max(np.abs(ls / lf - 1)) * 100


def safe_name(s):
    return "".join(c if c.isalnum() or c in "-*." else "_" for c in str(s))


def main():

    parser = argparse.ArgumentParser(description="Generate coherent interface")

    parser.add_argument("--subs", required=True, help="substrate structure")

    parser.add_argument("--film", required=True, help="film structure")

    parser.add_argument("--sm", nargs=3, type=int, required=True)

    parser.add_argument("--fm", nargs=3, type=int, required=True)

    parser.add_argument("--st", type=int, default=1)

    parser.add_argument("--ft", type=int, default=1)

    parser.add_argument("--gap", type=float, default=2.5)

    parser.add_argument("--shift", nargs=2, type=float, default=[0, 0])

    parser.add_argument("--output", default=None)

    args = parser.parse_args()

    subs = Structure.from_file(args.subs)
    film = Structure.from_file(args.film)
    if args.output is None:
        args.output = (
            f"{Path(args.subs).stem}_"
            f"{args.sm[0]}{args.sm[1]}{args.sm[2]}_"
            f"{Path(args.film).stem}_"
            f"{args.fm[0]}{args.fm[1]}{args.fm[2]}_"
            f"sub{args.st}_"
            f"film{args.ft}_"
            f"offset{args.shift[0]}_{args.shift[1]}"
        )

    zslgen = ZSLGenerator(
        max_area=200, max_length_tol=0.03, max_angle_tol=0.02, max_area_ratio_tol=0.08,bidirectional=True
    )

    builder = CoherentInterfaceBuilder(
        substrate_structure=subs,
        film_structure=film,
        substrate_miller=tuple(args.sm),
        film_miller=tuple(args.fm),
        termination_ftol=0.5,
        zslgen=zslgen,
        filter_out_sym_slabs=True,
        label_index=False,
    )

    outdir = Path(args.output)
    outdir.mkdir(exist_ok=True)

    print(f"Found {len(builder.terminations)} terminations")
    print(f"Found {len(builder.zsl_matches)} ZSL matches\n")

    for i, match in enumerate(builder.zsl_matches):
        print(
            f"Match {i:2d} "
            f"Area={match.match_area:.2f} "
            f"Misfit={calc_zsl_misfit(match):.2f}%"
        )

    for term in builder.terminations:
        print(f"\nTermination: {term}")

        interfaces = list(
            builder.get_interfaces(
                termination=term,
                gap=args.gap,
                vacuum_over_film=20,
                film_thickness=args.ft,
                substrate_thickness=args.st,
                in_plane_offset=tuple(args.shift),
                in_layers=True
            )
        )

        print(f"Generated {len(interfaces)} interfaces")

        unique = []

        for i, interface in enumerate(interfaces):
            
            imatch = i % len(builder.zsl_matches)
            misfit = calc_zsl_misfit(builder.zsl_matches[imatch])

            name = (
                f"{safe_name(term[0])}_"
                f"{safe_name(term[1])}_"
                f"M{imatch}_"
                f"misfit{misfit:.2f}%_"
                f"{len(unique) - 1}.vasp"
            )

            outfile = outdir / name

            print(f"Writing {outfile} (atoms={len(interface)}, misfit={misfit:.2f}%)")

            Poscar(interface).write_file(outfile)


if __name__ == "__main__":
    main()
