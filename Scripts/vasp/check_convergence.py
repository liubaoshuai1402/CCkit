# CCkit 功能说明：扫描 OUTCAR，分别报告 VASP 离子收敛和正常结束的状态及数量。
"""Check the ionic convergence and normal termination markers in OUTCAR files."""

import argparse
from pathlib import Path


STOPPING_PHRASE = "reached required accuracy - stopping structural energy minimisation"
COMPLETION_MARKER = "General timing and accounting"


def read_outcar_status(path: Path) -> tuple[bool, bool]:
    """Return whether the ionic convergence and timing summary markers appear."""
    overlap = max(len(STOPPING_PHRASE), len(COMPLETION_MARKER)) - 1
    tail = ""
    converged = False
    completed = False
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        while chunk := handle.read(65536):
            text = tail + chunk
            converged = converged or STOPPING_PHRASE in text
            completed = completed or COMPLETION_MARKER in text
            if converged and completed:
                break
            tail = text[-overlap:]
    return converged, completed


def find_outcars(root: Path, recursive: bool) -> list[Path]:
    """Return sorted absolute paths of all OUTCAR files below root."""
    if recursive:
        paths = (path for path in root.rglob("OUTCAR") if path.is_file())
    else:
        paths = (path for path in root.glob("*/OUTCAR") if path.is_file())
    return sorted({path.resolve() for path in paths}, key=str)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check VASP ionic convergence and normal termination in OUTCAR files"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Directory to search for OUTCAR files (default: current directory)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only check immediate subdirectories instead of searching recursively",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"Root directory does not exist: {root}")

    outcars = find_outcars(root, recursive=not args.no_recursive)
    if not outcars:
        print(f"No OUTCAR files found below: {root}")
        return

    total = len(outcars)
    converged_count = 0
    completed_count = 0
    unreadable_count = 0

    print("========== VASP Convergence and Completion Check ==========")
    print(f"Root  : {root}")
    print(f"Found : {total} OUTCAR(s)")
    print()
    print(f"{'Convergence':<14} {'Termination':<20} OUTCAR")
    for path in outcars:
        try:
            converged, completed = read_outcar_status(path)
        except OSError as error:
            unreadable_count += 1
            print(f"Error reading {path}: {error}")
            continue

        converged_count += converged
        completed_count += completed
        convergence_status = "Converged" if converged else "Not converged"
        termination_status = "Completed" if completed else "No completion marker"
        print(f"{convergence_status:<14} {termination_status:<20} {path}")

    print()
    print(f"Summary: {converged_count}/{total} calculations converged")
    print(f"         {completed_count}/{total} calculations completed normally")
    print(f"         {total - completed_count - unreadable_count}/{total} have no completion marker")
    if unreadable_count:
        print(f"         {unreadable_count}/{total} OUTCAR files could not be read")


if __name__ == "__main__":
    main()
