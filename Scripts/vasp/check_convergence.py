# CCkit 功能说明：
# 递归查找 OUTCAR，通过"reached required accuracy - stopping structural energy
# minimisation"判断 VASP 计算是否收敛，并输出 OUTCAR 绝对路径与收敛状态。
import argparse
from pathlib import Path


STOPPING_PHRASE = "reached required accuracy - stopping structural energy minimisation"


def file_contains(path: Path, text: str) -> bool:
    """Return whether text appears in path, streaming to handle huge OUTCARs."""
    overlap = len(text) - 1
    tail = ""
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        while chunk := handle.read(65536):
            if text in tail + chunk:
                return True
            tail = chunk[-overlap:] if overlap else ""
    return False


def find_outcars(root: Path, recursive: bool) -> list[Path]:
    """Return sorted absolute paths of all OUTCAR files below root."""
    if recursive:
        paths = (path for path in root.rglob("OUTCAR") if path.is_file())
    else:
        paths = (path for path in root.glob("*/OUTCAR") if path.is_file())
    return sorted({path.resolve() for path in paths}, key=str)


def check_convergence(path: Path) -> str:
    """Return convergence status for one OUTCAR file."""
    try:
        return "Converged" if file_contains(path, STOPPING_PHRASE) else "Not converged"
    except OSError as error:
        return f"Error ({error})"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check whether VASP calculations converged by scanning OUTCAR files"
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

    results = [(path, check_convergence(path)) for path in outcars]
    converged = sum(status == "Converged" for _, status in results)

    print("========== VASP Convergence Check ==========")
    print(f"Root  : {root}")
    print(f"Found : {len(results)} OUTCAR(s), {converged} converged")
    print()
    for path, status in results:
        print(f"{status:<14}{path}")
    print()
    print(f"Summary: {converged}/{len(results)} calculations converged")


if __name__ == "__main__":
    main()
