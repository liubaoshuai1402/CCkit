# CCkit 功能说明：
# 递归查找包含 POSCAR 的计算目录，并批量分发 VASP 输入文件和可选任务脚本。
import argparse
import shutil
from pathlib import Path


REQUIRED_INPUTS = ("INCAR", "POTCAR")


def find_poscar_directories(root):
    """Return subdirectories below root that contain a POSCAR file."""
    return sorted(
        {
            poscar.parent
            for poscar in root.rglob("POSCAR")
            if poscar.is_file() and poscar.parent != root
        },
        key=lambda path: str(path).lower(),
    )


def collect_source_files(root, job_name):
    """Validate required inputs and collect available optional files."""
    missing = [name for name in REQUIRED_INPUTS if not (root / name).is_file()]
    if missing:
        missing_text = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required input files in {root}: {missing_text}"
        )

    source_files = [root / name for name in REQUIRED_INPUTS]

    kpoints_file = root / "KPOINTS"
    if kpoints_file.is_file():
        source_files.append(kpoints_file)
    else:
        print(f"Optional KPOINTS not found, skip: {kpoints_file}")

    job_file = root / job_name
    if job_file.is_file():
        source_files.append(job_file)
    else:
        print(f"Optional job script not found, skip: {job_file}")

    return source_files


def distribute_files(source_files, target_directories):
    """Copy source files into every target directory, replacing old copies."""
    for target in target_directories:
        for source in source_files:
            shutil.copy2(source, target / source.name)
        print(f"Prepared: {target}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Find POSCAR directories recursively and distribute VASP input files."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Source and search root directory (default: current directory)",
    )
    parser.add_argument(
        "--job",
        default="job.slurm",
        help="Optional job script name in the root directory (default: job.slurm)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"Root directory does not exist: {root}")

    try:
        source_files = collect_source_files(root, args.job)
    except FileNotFoundError as error:
        parser.error(str(error))

    target_directories = find_poscar_directories(root)
    if not target_directories:
        print(f"No POSCAR directories found below: {root}")
        return

    distribute_files(source_files, target_directories)
    print(
        f"Completed: copied {len(source_files)} files to "
        f"{len(target_directories)} POSCAR directories."
    )


if __name__ == "__main__":
    main()
