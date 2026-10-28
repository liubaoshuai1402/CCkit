# CCkit 功能说明：
# 列出 VASP 目录待删除文件，确认后清理，并支持额外保留文件。
"""Clean current-directory files only after explicit selection and confirmation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence


KEEP_PREFIXES = ("INCAR", "KPOINTS", "POSCAR", "POTCAR")


def clean_files(path: Path, remain: Sequence[str] = ()) -> None:
    """Preview files outside the keep rules and unlink them only after 'y'."""
    keep_names = set(remain)
    candidates = sorted(
        (
            entry
            for entry in path.iterdir()
            if not entry.is_dir()
            and not entry.name.startswith(KEEP_PREFIXES)
            and entry.name not in keep_names
        ),
        key=lambda entry: entry.name,
    )
    print(f"Directory to clean: {path}")
    print(f"Keep filename prefixes: {', '.join(KEEP_PREFIXES)}")
    if keep_names:
        print(f"Also keep exact filenames: {sorted(keep_names)!r}")
    if not candidates:
        print("No files to delete.")
        return

    print(f"Files to delete ({len(candidates)}):")
    for entry in candidates:
        print(f"  {str(entry)!r}")

    try:
        answer = input("Permanently delete all listed files? (y/n): ")
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled; no files deleted.")
        return
    if answer.strip().lower() != "y":
        print("Cancelled; no files deleted.")
        return

    # Delete only the displayed snapshot; do not rescan after confirmation.
    for entry in candidates:
        try:
            entry.unlink()
        except OSError as error:
            raise OSError(
                f"Cannot delete {str(entry)!r}: {error}. "
                "Cleanup stopped; previously reported removals are permanent."
            ) from error
        print(f"Removed: {str(entry)!r}")
    print(f"Completed: deleted {len(candidates)} files from {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clean VASP files in the current directory. Mode 0 lists files "
            "and requires 'y' before deletion. Directories are skipped; "
            "filename prefixes INCAR, KPOINTS, POSCAR and POTCAR are kept. "
            "Without a mode, only help is shown."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "mode", nargs="?", choices=("0",),
        help="0: clean with the default keep rules and any additional -remain files",
    )
    parser.add_argument(
        "-remain", "--remain", nargs="+", action="extend", default=[],
        metavar="FILE",
        help=(
            "Additional exact filenames to keep in the current directory "
            "(space-separated, repeatable; no paths or wildcards)"
        ),
    )
    args = parser.parse_args()
    if args.mode is None:
        if args.remain:
            parser.error("-remain requires mode 0")
        parser.print_help()
        return

    root = Path.cwd().resolve()
    for name in args.remain:
        if (
            not name
            or name in (".", "..")
            or "/" in name
            or "\\" in name
            or ":" in name
        ):
            parser.error(f"-remain requires a filename without a path: {name!r}")
        entry = root / name
        if not entry.exists() and not entry.is_symlink():
            parser.error(f"File requested with -remain does not exist: {name!r}")
        if entry.is_dir():
            parser.error(
                f"-remain expects a file; directories are already kept: {name!r}"
            )

    try:
        clean_files(root, args.remain)
    except OSError as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
