# CCkit 功能说明：从单个 OUTCAR 按离子步间隔提取能量、力和应力，写入扩展 XYZ。
"""Sample ionic-step data from one OUTCAR into an extended XYZ dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from ase import Atoms
from ase.io import read, write


def collect_ionic_steps(
    input_path: Path,
    interval: int,
    skip: int,
    flag: str | None = None,
) -> list[Atoms]:
    """Read one OUTCAR and sample its ionic structures after an initial skip."""
    frames = read(input_path, index=":", format="vasp-out")
    selected = frames[skip::interval]
    for atoms in selected:
        atoms.info["energy"] = atoms.get_potential_energy(force_consistent=True)
        atoms.info["stress"] = atoms.get_stress(voigt=True)
        atoms.arrays["force"] = atoms.get_forces()
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
        description="Sample ionic steps from one OUTCAR into an extended XYZ dataset."
    )
    parser.add_argument(
        "input", nargs="?", type=Path, default=Path("OUTCAR"),
        help="OUTCAR filename in the current calculation directory (default: OUTCAR)",
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

    input_path = args.input.expanduser().resolve()
    if input_path.parent != Path.cwd().resolve():
        parser.error("Input must be an OUTCAR file in the current directory.")
    if not input_path.is_file():
        parser.error(f"OUTCAR file not found: {input_path}")
    output_path = resolve_output(args.output, input_path)
    if output_path == input_path:
        parser.error("Output path must differ from the OUTCAR input.")
    try:
        frames = collect_ionic_steps(input_path, args.interval, args.skip, args.flag)
        if not frames:
            parser.error(
                f"No ionic steps remain after skipping {args.skip} steps in {input_path}."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write(output_path, frames, format="extxyz")
    except (OSError, ValueError, IndexError, RuntimeError) as error:
        parser.error(f"Cannot convert {input_path}: {error}")

    print(f"Read one OUTCAR: {input_path}")
    print(f"Skipped {args.skip} initial ionic steps; sampled every {args.interval} step(s).")
    print(f"Wrote {len(frames)} configurations to {output_path}")


if __name__ == "__main__":
    main()
