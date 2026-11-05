# CCkit 功能说明：备份 INCAR，调整预弛豫参数并注释启用的 ADDGRID；缺少必需参数时报错。
"""Rename the original INCAR to INCAR-back and write pre-relaxation settings.

pymatgen's INCAR writer reformats the file, so narrow byte replacements are
used to preserve comments, whitespace and line endings. No missing tags are added.
Enabled ADDGRID assignments are commented out, splitting a line only when needed
to keep following assignments active.
"""

from __future__ import annotations

import argparse
import codecs
import re
from pathlib import Path


PRE_RELAX_SETTINGS = {
    b"EDIFF": b"5E-05",
    b"NSW": b"5",
    b"PREC": b"N",
    b"KSPACING": b"0.25",
}
SETTING_PATTERN = re.compile(
    rb"(?P<prefix>(?:^|;)[ \t]*(?P<tag>[A-Za-z][A-Za-z0-9_]*)[ \t]*=[ \t]*)"
    rb"""(?P<value>(?:"[^"\r\n]*"|'[^'\r\n]*'|[^"'#!;\r\n])*?)"""
    rb"(?P<suffix>[ \t]*)(?=;|#|!|\r|\n|$)|[#!][^\r\n]*"
)


def comment_enabled_addgrid(line: bytes, newline: bytes) -> bytes:
    """Comment true ADDGRID assignments without disabling subsequent settings."""
    matches = list(SETTING_PATTERN.finditer(line))
    edits: list[tuple[int, int, bytes]] = []
    for index, match in enumerate(matches):
        if match["tag"] is None or match["tag"].upper() != b"ADDGRID":
            continue
        value = match["value"].strip()
        if value[:1] in (b'"', b"'") and value[-1:] == value[:1]:
            value = value[1:-1].strip()
        if b"\\" in value:
            raise ValueError("Put the value of ADDGRID on one line before retrying.")
        if value.upper() not in (b".TRUE.", b"TRUE", b".T.", b"T"):
            continue

        edits.append((match.start("tag"), match.start("tag"), b"#"))
        if index + 1 < len(matches) and matches[index + 1]["tag"] is not None:
            # A # comments through the end of the physical line. Keep the
            # separator, but put subsequent assignments on a new line.
            edits.append((match.end(), match.end() + 1, b";" + newline))

    # Apply from right to left so all offsets refer to the original line.
    for start, end, replacement in sorted(
        edits, key=lambda edit: edit[0], reverse=True
    ):
        line = line[:start] + replacement + line[end:]
    return line


def replace_settings(contents: bytes) -> bytes:
    """Replace active scalar assignments without altering surrounding bytes.

    Tags are case-insensitive, semicolon-separated assignments are supported,
    and every active duplicate is updated. Commented tags do not count as present.
    Enabled ADDGRID entries are commented; missing or false ADDGRID is unchanged.
    """
    found: set[bytes] = set()

    def replace(match: re.Match[bytes]) -> bytes:
        # Consume other assignments (including quoted text) and comments intact.
        if match["tag"] is None:
            return match[0]
        tag = match["tag"].upper()
        if tag not in PRE_RELAX_SETTINGS:
            return match[0]
        value = match["value"]
        if not value.strip():
            return match[0]
        if b"\\" in value:
            raise ValueError(
                f"Put the value of {tag.decode('ascii')} on one line before retrying."
            )
        found.add(tag)
        new_value = PRE_RELAX_SETTINGS[tag]
        if value[:1] in (b'"', b"'") and value[-1:] == value[:1]:
            new_value = value[:1] + new_value + value[-1:]
        return match["prefix"] + new_value + match["suffix"]

    bom = b""
    if contents.startswith(codecs.BOM_UTF8):
        bom = codecs.BOM_UTF8
        contents = contents[len(bom):]

    newline_match = re.search(rb"\r\n|\r|\n", contents)
    default_newline = newline_match[0] if newline_match else b"\n"
    updated_lines = []
    for line in contents.splitlines(keepends=True):
        newline = next(
            (ending for ending in (b"\r\n", b"\n", b"\r") if line.endswith(ending)),
            default_newline,
        )
        updated_lines.append(
            comment_enabled_addgrid(SETTING_PATTERN.sub(replace, line), newline)
        )

    missing = [tag.decode("ascii") for tag in PRE_RELAX_SETTINGS if tag not in found]
    if missing:
        raise ValueError(f"Missing required INCAR parameters: {', '.join(missing)}.")
    return bom + b"".join(updated_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Back up INCAR as INCAR-back and replace existing EDIFF, NSW, PREC "
            "and KSPACING with 5E-05, 5, N and 0.25. All four tags must exist. "
            "Comment out enabled ADDGRID entries. Preserve formatting, adding "
            "a line break only to keep settings after ADDGRID active."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "incar", nargs="?", type=Path, default=Path("INCAR"),
        help=(
            "INCAR path (default: ./INCAR); INCAR-back is created beside it "
            "and must not already exist"
        ),
    )
    args = parser.parse_args()

    incar_path = args.incar.expanduser().resolve()
    backup_path = incar_path.with_name("INCAR-back")
    if not incar_path.is_file():
        parser.error(f"INCAR file not found: {incar_path}")
    if backup_path.exists() or backup_path.is_symlink():
        parser.error(f"Backup already exists; move it before retrying: {backup_path}")

    try:
        updated_contents = replace_settings(incar_path.read_bytes())
    except (OSError, ValueError) as error:
        parser.error(f"Cannot prepare {incar_path}: {error} No files changed.")

    try:
        incar_path.rename(backup_path)
    except OSError as error:
        parser.exit(1, f"Cannot back up {incar_path} to {backup_path}: {error}\n")
    try:
        incar_path.write_bytes(updated_contents)
    except OSError as error:
        parser.exit(
            1,
            f"Cannot write {incar_path}: {error}\n"
            f"The original INCAR is preserved in {backup_path}.\n",
        )

    print(f"Original INCAR: {backup_path}")
    print(f"Pre-relaxation INCAR: {incar_path}")
    print("Updated: EDIFF = 5E-05, NSW = 5, PREC = N, KSPACING = 0.25")


if __name__ == "__main__":
    main()
