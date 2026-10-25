# CCkit 功能说明：
# 将轨迹拆分为 POSCAR；输入文件旁有 INCAR 时同时准备 VASP 单点计算目录。
"""Write one POSCAR per trajectory frame, optionally copying VASP inputs."""

import argparse
import shutil
from pathlib import Path
from typing import Optional, Sequence

from ase import Atoms
from ase.io import read
from ase.io.vasp import write_vasp


def collect_vasp_inputs(input_dir: Path, submit: Optional[str], copy_kpoints: bool) -> list[Path]:
    """Return VASP inputs, or an empty list when INCAR is absent."""
    incar = input_dir / "INCAR"
    if not incar.is_file():
        return []

    if not submit:
        raise ValueError("--submit is required when INCAR is present")

    source_files = [incar, input_dir / "POTCAR"]
    if copy_kpoints:
        source_files.append(input_dir / "KPOINTS")
    source_files.append(input_dir / submit)

    for source in source_files:
        if not source.is_file():
            raise FileNotFoundError(f"Required VASP input not found: {source}")
    return source_files


def prepare_sp(
    structures: Sequence[Atoms], input_path: Path, submit: Optional[str], copy_kpoints: bool = False
) -> None:
    """Create numbered POSCAR directories beside the input trajectory."""
    input_dir = input_path.resolve().parent
    source_files = collect_vasp_inputs(input_dir, submit, copy_kpoints)
    singlepoint_path = input_dir / "singlepoint"

    for number, atoms in enumerate(structures):
        number_path = singlepoint_path / str(number)
        number_path.mkdir(parents=True)
        for source in source_files:
            shutil.copy2(source, number_path / source.name)
        write_vasp(number_path / "POSCAR", atoms, direct=True, sort=True)

    print(f"Created {len(structures)} POSCAR directories in {singlepoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a trajectory into POSCAR files; copy VASP inputs when INCAR is present."
    )
    parser.add_argument("input", type=Path, help="Input trajectory with cell information")
    parser.add_argument("--slice", default=":", help="ASE frame slice (default: all frames)")
    parser.add_argument(
        "--submit", help="Submission script beside the input (required only when INCAR exists)"
    )
    parser.add_argument(
        "--KPOINTS", action="store_true", help="Copy KPOINTS when INCAR exists"
    )
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input trajectory not found: {args.input}")
    structures = read(args.input, index=args.slice)
    if isinstance(structures, Atoms):
        structures = [structures]
    if not structures:
        parser.error("The selected trajectory slice contains no structures")
    try:
        prepare_sp(structures, args.input, args.submit, args.KPOINTS)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
