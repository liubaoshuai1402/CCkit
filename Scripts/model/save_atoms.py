# CCkit 功能说明：保留指定原子周围给定半径内的原子，并另存为结构文件。
"""Extract one local structure using minimum-image distances when periodic."""

import argparse
import math
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write
from ase.io.formats import (
    UnknownFileTypeError,
    filetype,
    get_compression,
    get_ioformat,
    open_with_compression,
)


def select_atoms(atoms: Atoms, center: int, radius: float) -> Atoms:
    """Keep atoms within radius in Angstrom of the zero-based center index."""
    if not 0 <= center < len(atoms):
        raise ValueError(f"Center index must be in [0, {len(atoms)}), got {center}")
    distances = atoms.get_distances(center, np.arange(len(atoms)), mic=True)
    if not np.isfinite(distances).all():
        raise ValueError("Structure contains non-finite distances from the center atom")
    # The mask keeps the original atom order and stored coordinates.
    return atoms[distances <= radius]


def structure_format(path: Path, fallback: str | None = None) -> str:
    """Infer the ASE format, using fallback for an unnamed output format."""
    uncompressed_name, _ = get_compression(str(path))
    suffix = Path(uncompressed_name).suffix.lower()
    if suffix == ".vasp":
        return "vasp"
    if suffix == ".extxyz":
        return "extxyz"
    try:
        return filetype(str(path), read=fallback is None)
    except UnknownFileTypeError:
        if fallback is None:
            raise
        return fallback


def write_new_structure(path: Path, atoms: Atoms, format_name: str) -> None:
    """Write a new file exclusively and remove an incomplete output on failure."""
    output_format = get_ioformat(format_name)
    if not output_format.can_write or not output_format.acceptsfd:
        raise ValueError(f"Cannot write {format_name} as a single file. Use .vasp or .xyz.")
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "xb" if output_format.isbinary else "xt"
    handle = open_with_compression(str(path), mode)
    try:
        with handle:
            write(handle, atoms, format=format_name)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Save the atoms within a radius of a selected atom as a new structure."
    )
    parser.add_argument("input", type=Path, help="Input structure file (reads the first frame)")
    parser.add_argument("center", type=int, help="Center atom index (0-based)")
    parser.add_argument("radius", type=float, help="Inclusive radius in Angstrom (non-negative)")
    parser.add_argument(
        "-o", "--output",
        help="New output file. Bare names go beside the input. Defaults to POSCAR or ExtXYZ.",
    )
    args = parser.parse_args()

    if not math.isfinite(args.radius) or args.radius < 0:
        parser.error("radius must be finite and non-negative")
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        parser.error(f"Input structure not found: {input_path}")

    try:
        input_format = structure_format(input_path)
        atoms = read(input_path, index=0, format=input_format, do_not_split_by_at_sign=True)
        selected = select_atoms(atoms, args.center, args.radius)
    except (OSError, ValueError, RuntimeError, IndexError, UnknownFileTypeError) as error:
        parser.error(f"Cannot select atoms from {input_path}: {error}")

    default_format = "vasp" if input_format == "vasp" else "extxyz"
    suffix = f"_saved_{args.center}_r{args.radius:g}"
    if args.output is None:
        name = f"POSCAR{suffix}" if default_format == "vasp" else f"{input_path.stem}{suffix}.xyz"
        output_path = input_path.with_name(name)
    else:
        output_path = Path(args.output).expanduser()
        if not output_path.is_absolute() and not any(sep in args.output for sep in ("/", "\\")):
            output_path = input_path.parent / output_path

    try:
        output_format = structure_format(output_path, fallback=default_format)
        write_new_structure(output_path, selected, output_format)
    except FileExistsError:
        parser.error(f"Output already exists: {output_path.absolute()}")
    except (OSError, ValueError, RuntimeError, UnknownFileTypeError) as error:
        parser.error(f"Cannot write {output_path.absolute()}: {error}")

    print(f"Kept {len(selected)}/{len(atoms)} atoms within {args.radius:g} Angstrom of atom {args.center}.")
    print(f"Output: {output_path.absolute()}")


if __name__ == "__main__":
    main()
