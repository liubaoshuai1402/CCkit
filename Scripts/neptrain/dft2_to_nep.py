# CCkit 功能说明：从单个 OUTCAR 或 VASP XML 按离子步间隔提取计算结果，写入扩展 XYZ。
"""Sample ionic-step data from one VASP result file into extended XYZ."""

from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree.ElementTree import ParseError

from ase import Atoms
from ase.io import read, write
from ase.units import GPa


def collect_ionic_steps(
    input_path: Path,
    interval: int,
    skip: int,
    flag: str | None = None,
    file_format: str = "auto",
) -> list[Atoms]:
    """Read one OUTCAR/XML file and sample its ionic structures after a skip."""
    if file_format == "auto":
        file_format = "xml" if input_path.suffix.lower() == ".xml" else "outcar"
    ase_format = {"outcar": "vasp-out", "xml": "vasp-xml"}[file_format]
    frames = read(input_path, index=":", format=ase_format)
    selected = frames[skip::interval]
    for atoms in selected:
        atoms.info["energy"] = atoms.get_potential_energy(force_consistent=True)
        # ASE stress is tensile-positive in eV/Angstrom^3;
        # NEP virial is compressive-positive in eV, stored as a full 3x3 tensor.
        volume = atoms.get_volume()
        virial = -atoms.get_stress(voigt=False) * volume
        atoms.info["virial"] = virial
        # Normalize by volume and use the same nine-component order as virial.
        atoms.info["virial_GPa"] = (virial / volume / GPa).reshape(9, order="F")
        atoms.arrays["forces"] = atoms.get_forces()
        if flag is not None:
            atoms.info["config_type"] = flag
        atoms.calc = None
    return selected


def resolve_output(output: Path, input_path: Path) -> Path:
    """Resolve bare output names beside the input file."""
    output = output.expanduser()
    if not output.is_absolute() and output.parent == Path("."):
        output = input_path.parent / output
    return output.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample ionic steps from one OUTCAR/XML file into extended XYZ."
    )
    parser.add_argument(
        "input", nargs="?", type=Path,
        help="Result filename in the current directory (default: OUTCAR, or XML with --format xml)",
    )
    parser.add_argument(
        "--format", choices=("auto", "outcar", "xml"), default="auto",
        help="Input format; auto recognizes .xml and otherwise reads OUTCAR (default: auto)",
    )
    parser.add_argument(
        "--interval", type=int, default=1,
        help="Keep every Nth ionic step after skipping (default: 1, keep every step)",
    )
    parser.add_argument(
        "--skip", type=int, default=0,
        help="Number of initial ionic steps to discard before sampling (default: 0)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("dataset.xyz"),
        help="Output extended XYZ; default and bare filenames go beside input (default: dataset.xyz)",
    )
    parser.add_argument(
        "--flag", help="Optional config_type label applied to each selected frame",
    )
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be a positive integer")
    if args.skip < 0:
        parser.error("--skip must be a non-negative integer")

    if args.input is None:
        input_names = ("vasp.xml", "vasprun.xml") if args.format == "xml" else ("OUTCAR",)
        args.input = next(
            (Path(name) for name in input_names if Path(name).is_file()), Path(input_names[0])
        )
    input_path = args.input.expanduser().resolve()
    if input_path.parent != Path.cwd().resolve():
        parser.error("Input must be an OUTCAR/XML result file in the current directory.")
    if not input_path.is_file():
        parser.error(f"VASP result file not found: {input_path}")
    output_path = resolve_output(args.output, input_path)
    if output_path == input_path:
        parser.error("Output path must differ from the VASP result input.")
    try:
        frames = collect_ionic_steps(input_path, args.interval, args.skip, args.flag, args.format)
        if not frames:
            parser.error(
                f"No ionic steps remain after skipping {args.skip} steps in {input_path}."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # ASE extxyz writes atomic positions with %16.8f (eight decimal places).
        write(output_path, frames, format="extxyz")
    except (OSError, ValueError, IndexError, RuntimeError, ParseError) as error:
        parser.error(f"Cannot convert {input_path}: {error}")

    print(f"Read one VASP result file: {input_path}")
    print(f"Skipped {args.skip} initial ionic steps; sampled every {args.interval} step(s).")
    print(f"Wrote {len(frames)} configurations to {output_path}")


if __name__ == "__main__":
    main()
