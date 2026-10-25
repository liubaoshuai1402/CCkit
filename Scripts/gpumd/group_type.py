# CCkit 功能说明：
# 按元素类型为 XYZ 文件夹中每一帧的原子写入整数 group 标签。
"""Label atoms by element in every XYZ trajectory in one directory."""

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
from ase.io import iread, write


DEFAULT_ORDER = ("H", "O", "Zr", "Y")
XYZ_SUFFIXES = {".xyz", ".extxyz"}


def find_xyz_files(directory: Path) -> list[Path]:
    """Find input trajectories directly inside a directory, excluding generated files."""
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in XYZ_SUFFIXES
            and not path.stem.lower().endswith("_group")
        ),
        key=lambda path: path.name.lower(),
    )


def output_path(input_path: Path) -> Path:
    """Place a labeled trajectory beside its source file."""
    return input_path.with_name(f"{input_path.stem}_group{input_path.suffix}")


def collect_elements(paths: Sequence[Path]) -> set[str]:
    """Read all frames once to find every element used in the directory."""
    elements: set[str] = set()
    for path in paths:
        frame_count = 0
        try:
            for atoms in iread(path, index=":"):
                frame_count += 1
                elements.update(atoms.get_chemical_symbols())
        except (OSError, ValueError) as error:
            raise ValueError(f"Cannot read {path}: {error}") from error
        if frame_count == 0:
            raise ValueError(f"No structures found in {path}")
    return elements


def make_group_ids(elements: set[str], preferred_order: Sequence[str]) -> dict[str, int]:
    """Assign contiguous IDs, honoring the requested element order first."""
    ordered = [symbol for symbol in preferred_order if symbol in elements]
    ordered.extend(sorted(elements.difference(ordered)))
    return {symbol: index for index, symbol in enumerate(ordered)}


def label_file(input_path: Path, groups: dict[str, int]) -> tuple[Path, int]:
    """Stream labeled frames to an extended XYZ file beside the input."""
    destination = output_path(input_path)
    frame_count = 0
    try:
        with destination.open("w", encoding="utf-8") as handle:
            for atoms in iread(input_path, index=":"):
                symbols = atoms.get_chemical_symbols()
                atoms.set_array("group", np.fromiter((groups[s] for s in symbols), dtype=int))
                write(handle, atoms, format="extxyz")
                frame_count += 1
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot label {input_path}: {error}") from error
    return destination, frame_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add element-based group IDs to every XYZ trajectory in a folder."
    )
    parser.add_argument("directory", type=Path, help="Folder containing XYZ or extXYZ files")
    parser.add_argument(
        "--order", nargs="+", default=DEFAULT_ORDER, metavar="ELEMENT",
        help="Preferred element order for group IDs (default: H O Zr Y)",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Replace existing *_group XYZ outputs"
    )
    args = parser.parse_args()

    directory = args.directory.expanduser().resolve()
    if not directory.is_dir():
        parser.error(f"XYZ directory does not exist: {directory}")
    if len(args.order) != len(set(args.order)):
        parser.error("--order must not contain duplicate elements")

    inputs = find_xyz_files(directory)
    if not inputs:
        parser.error(f"No XYZ or extXYZ inputs found directly in {directory}")
    if not args.overwrite:
        existing = [output_path(path) for path in inputs if output_path(path).exists()]
        if existing:
            parser.error(f"Output already exists: {existing[0]} (use --overwrite to replace it)")

    try:
        groups = make_group_ids(collect_elements(inputs), args.order)
        for path in inputs:
            destination, frame_count = label_file(path, groups)
            print(f"Labeled {frame_count} frame(s): {destination}")
    except ValueError as error:
        parser.error(str(error))

    mapping = ", ".join(f"{symbol}={index}" for symbol, index in groups.items())
    print(f"Group IDs: {mapping}")


if __name__ == "__main__":
    main()
