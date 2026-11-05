# CCkit 功能说明：
# 按离子步间隔提取 OUTCAR、vasprun.xml/vasp.xml 或 XDATCAR，准备单点计算目录。
"""Write sampled VASP ionic structures to POSCAR jobs in the current directory.

Sampling starts at the first ionic structure. Output jobs are numbered from
zero, retaining atom order, cells and constraints supplied by ASE's readers.
Relative output paths resolve from the command's working directory.
Optional calculation inputs are collected independently from that directory.
"""

import argparse
import shutil
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Optional

from ase import Atoms
from ase.io import iread
from ase.io.vasp import write_vasp


VASP_FORMATS = {"outcar": "vasp-out", "xml": "vasp-xml", "xdatcar": "vasp-xdatcar"}
INPUT_FORMATS = {
    "outcar": "outcar",
    "vasprun.xml": "xml",
    "vasp.xml": "xml",
    "xdatcar": "xdatcar",
}


def resolve_format(input_path: Path, file_format: str) -> str:
    """Map a known filename or explicit format to an ASE VASP reader."""
    if file_format == "auto":
        name = input_path.name.lower()
        if name.endswith(".gz"):
            name = name[:-3]
        if name not in INPUT_FORMATS:
            raise ValueError(
                "Unknown VASP filename; specify --format outcar, xml or xdatcar "
                "for a renamed input."
            )
        file_format = INPUT_FORMATS[name]
    return VASP_FORMATS[file_format]


def collect_vasp_inputs(source_dir: Path, submit: Optional[str], copy_kpoints: bool) -> list[Path]:
    """Collect each existing optional input independently from the working directory."""
    sources = [source_dir / "INCAR", source_dir / "POTCAR"]
    if copy_kpoints:
        sources.append(source_dir / "KPOINTS")
    if submit:
        sources.append(source_dir / Path(submit).expanduser())
    return [source for source in sources if source.is_file()]


def read_ionic_structures(input_path: Path, file_format: str) -> Iterator[Atoms]:
    """Yield all ionic structures using ASE's parsers, in file order."""
    try:
        with closing(iread(
            input_path,
            index=":",
            format=file_format,
            do_not_split_by_at_sign=True,
        )) as structures:
            for atoms in structures:
                # ASE may return initialpos alone for an interrupted XML file.
                if file_format == "vasp-xml" and atoms.calc is None:
                    raise ValueError("XML contains an initial structure but no ionic steps")
                yield atoms
    except Exception as error:
        raise ValueError(f"Could not read ionic structures from {input_path}: {error}") from error


def prepare_sp(
    input_path: Path,
    output_dir: Path,
    file_format: str,
    interval: int,
    submit: Optional[str],
    copy_kpoints: bool,
) -> tuple[int, int]:
    """Create sampled jobs; return total structures read and POSCARs written."""
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError(f"Output already exists: {output_dir}. Choose another -o directory.")
    sources = collect_vasp_inputs(Path.cwd(), submit, copy_kpoints)

    total_count = 0
    converted_count = 0
    with closing(read_ionic_structures(input_path, file_format)) as structures:
        for source_index, atoms in enumerate(structures):
            total_count += 1
            if source_index % interval != 0:
                continue
            if not len(atoms):
                raise ValueError(f"Ionic structure at frame {source_index} has no atoms")
            if converted_count == 0:
                output_dir.mkdir(parents=True)
            job_dir = output_dir / str(converted_count)
            job_dir.mkdir()
            try:
                for source in sources:
                    shutil.copy2(source, job_dir / source.name)
                # Preserve the input species order so copied POTCARs stay aligned.
                write_vasp(job_dir / "POSCAR", atoms, direct=True, sort=False, vasp5=True)
            except (OSError, ValueError, RuntimeError) as error:
                raise ValueError(
                    f"Could not prepare frame {source_index} in {job_dir}: {error}"
                ) from error
            converted_count += 1

    if total_count == 0:
        raise ValueError(f"No ionic structures found in {input_path}")
    return total_count, converted_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sample VASP ionic structures into POSCAR jobs; "
            "independently copy available calculation inputs from the current directory."
        )
    )
    parser.add_argument("input", type=Path, help="OUTCAR, vasprun.xml/vasp.xml or XDATCAR (also .gz)")
    parser.add_argument(
        "--interval", type=int, default=1,
        help="Positive ionic-frame stride, starting at frame 0 (default: 1, all frames)",
    )
    parser.add_argument(
        "--format", choices=("auto", *VASP_FORMATS), default="auto",
        help="Input format; auto recognizes standard filenames (default: auto)",
    )
    parser.add_argument(
        "-o", "--output", type=str, default="singlepoint",
        help="New output directory, relative to the current directory (default: singlepoint)",
    )
    parser.add_argument(
        "--submit",
        help="Optional submission script relative to the current directory; copy if it exists",
    )
    parser.add_argument(
        "--KPOINTS", action="store_true",
        help="Copy KPOINTS from the current directory if it exists",
    )
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be a positive integer")
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        parser.error(f"Input file not found: {input_path}")
    output_dir = Path(args.output).expanduser().resolve()

    try:
        file_format = resolve_format(input_path, args.format)
        total_count, converted_count = prepare_sp(
            input_path, output_dir, file_format, args.interval, args.submit, args.KPOINTS
        )
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(f"{error}\nAny jobs already written remain in: {output_dir}")
    print(f"Read {total_count} ionic structures from {input_path}")
    print(f"Ionic-frame interval: {args.interval}")
    print(f"Converted {converted_count} structures to POSCAR")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
