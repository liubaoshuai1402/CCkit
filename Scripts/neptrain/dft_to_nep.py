# CCkit 功能说明：
# 递归读取 VASP OUTCAR 或 XML，并合并为可选带 config_type 标签的 NEP 训练 XYZ 数据集。
"""Collect VASP result files into an extended XYZ dataset using ASE."""

import argparse
import os
from pathlib import Path
from typing import Optional
from xml.etree.ElementTree import ParseError

from ase.io import read, write
from ase.units import GPa


def outcar_to_nepxyz(
    pos: str,
    output: str,
    flag: Optional[str] = None,
    file_format: str = "outcar",
    interval: int = 1,
) -> None:
    """Sample each calculation's result independently, starting at its first frame."""
    if interval <= 0:
        raise ValueError("--interval must be a positive integer")
    source_dir = Path(pos).expanduser().resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Calculation directory not found: {source_dir}")
    output_path = Path(output).expanduser()
    if not output_path.is_absolute() and output_path.parent == Path("."):
        output_path = source_dir / output_path
    output_path = output_path.resolve()
    ase_format = {"outcar": "vasp-out", "xml": "vasp-xml"}[file_format]
    input_names = ("OUTCAR",) if file_format == "outcar" else ("vasp.xml", "vasprun.xml")
    db = []
    source_count = 0
    total_count = 0
    for root, dirs, files in os.walk(source_dir):
        dirs.sort()
        input_name = next((name for name in input_names if name in files), None)
        if input_name is not None:
            input_path = Path(root) / input_name
            if input_path.resolve() == output_path:
                raise ValueError(f"Output path must differ from the VASP result input: {input_path}")
            frames = read(input_path, index=":", format=ase_format)
            total_count += len(frames)
            # Starting each file at index 0 also retains every single-step result.
            db.extend(frames[::interval])
            source_count += 1
    if not db:
        raise ValueError(f"No configurations found in {source_dir} for format {file_format}")
    for at in db:
        at.info['energy'] = at.get_potential_energy(force_consistent=True)
        # ASE stress is tensile-positive in eV/Angstrom^3;
        # NEP virial is compressive-positive in eV, stored as a full 3x3 tensor.
        volume = at.get_volume()
        virial = -at.get_stress(voigt=False) * volume
        at.info['virial'] = virial
        # Normalize by volume and use the same nine-component order as virial.
        at.info['virial_GPa'] = (virial / volume / GPa).reshape(9, order="F")
        at.arrays['forces'] = at.get_forces()
        if flag is not None:
            at.info['config_type'] = flag
        at.calc = None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # ASE extxyz writes atomic positions with %16.8f (eight decimal places).
    write(output_path, db, format="extxyz")
    print(f"Read {total_count} configurations from {source_count} {file_format} file(s).")
    print(f"Sampling interval: {interval}; wrote {len(db)} configurations.")
    print(f"Saved: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively convert VASP OUTCAR or XML results into extended XYZ for NEP"
    )
    parser.add_argument("--pos", type=str, default=".", help="Calculation root directory (default: .)")
    parser.add_argument(
        "--output", type=str, default="dataset.xyz",
        help="Output extended XYZ; default and bare filenames go under --pos (default: dataset.xyz)",
    )
    parser.add_argument(
        "--format", choices=("outcar", "xml"), default="outcar",
        help="Result files to collect: OUTCAR or vasp.xml/vasprun.xml (default: outcar)",
    )
    parser.add_argument(
        "--interval", type=int, default=1,
        help=(
            "Keep every Nth ionic step from the first step of each file; "
            "single-step files are kept (default: 1)"
        ),
    )
    parser.add_argument(
        "--flag", type=str,
        help="Set config_type to this label for every output configuration (optional)",
    )

    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be a positive integer")

    try:
        outcar_to_nepxyz(args.pos, args.output, args.flag, args.format, args.interval)
    except (OSError, ValueError, IndexError, RuntimeError, ParseError) as error:
        parser.error(f"Cannot convert {args.pos}: {error}")


if __name__ == "__main__":
    main()
