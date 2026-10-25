# CCkit 功能说明：读取 OUTCAR 最后一组晶胞应力，以 GPa 报告残余应力与优化状态。
"""Report the last VASP stress tensor, pressures, and relaxation context.

Stream OUTCAR (optionally gzip compressed), convert its kbar values to GPa,
and retain VASP's compression-positive sign convention. No dependencies
outside the Python standard library are required.
"""

from __future__ import annotations

import argparse
import gzip
import math
import re
from dataclasses import dataclass
from pathlib import Path

KBAR_TO_GPA = 0.1
COMPONENTS = ("xx", "yy", "zz", "xy", "yz", "zx")
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"
PRESSURE_PATTERN = re.compile(rf"external\s+pressure\s*=\s*({NUMBER})\s*kB", re.I)
PULAY_PATTERN = re.compile(rf"Pul+ay\s+stress\s*=\s*({NUMBER})\s*kB", re.I)
PSTRESS_PATTERN = re.compile(rf"\bPSTRESS\s*=\s*({NUMBER})", re.I)
ISIF_PATTERN = re.compile(r"\bISIF\s*=\s*(\d+)", re.I)
ACCURACY_MARKER = "reached required accuracy - stopping structural energy minimisation"


@dataclass
class StressReport:
    """Last printed stress values in GPa and the associated OUTCAR context."""

    components: tuple[float, ...] | None = None
    external_pressure: float | None = None
    pulay_stress: float | None = None
    pstress: float | None = None
    isif: int | None = None
    block_count: int = 0
    line_number: int | None = None
    accuracy_reached: bool = False
    normal_termination: bool = False


def parse_pressure(text: str) -> float:
    """Convert a finite VASP number in kbar, including D exponents, to GPa."""
    value = float(text.replace("D", "E").replace("d", "e")) * KBAR_TO_GPA
    if not math.isfinite(value):
        raise ValueError(f"Non-finite stress or pressure value: {text}")
    return value


def read_stress(path: Path) -> StressReport:
    """Stream the last stress block; reject an incomplete or malformed last block.

    VASP prints six entries in xx, yy, zz, xy, yz, zx order. The printed
    values are used directly, with no additional PSTRESS subtraction.
    """
    report = StressReport()
    last_block_error: str | None = None
    open_file = gzip.open if path.suffix.lower() == ".gz" else Path.open
    with open_file(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if match := ISIF_PATTERN.search(line):
                report.isif = int(match.group(1))
            if match := PSTRESS_PATTERN.search(line):
                report.pstress = parse_pressure(match.group(1))

            if "FORCE on cell" in line:
                # A later unfinished block must not silently reuse older data.
                report.components = None
                report.external_pressure = None
                report.pulay_stress = None
                report.line_number = None
                report.accuracy_reached = False
                report.normal_termination = False
                last_block_error = f"Incomplete final stress block starting at line {line_number}."

            if re.match(r"^\s*in\s+kB\b", line, re.I):
                report.block_count += 1
                report.components = None
                report.external_pressure = None
                report.pulay_stress = None
                report.accuracy_reached = False
                report.normal_termination = False
                report.line_number = line_number
                fields = re.sub(r"^\s*in\s+kB\s*", "", line, flags=re.I).split()
                try:
                    if len(fields) != 6:
                        raise ValueError("Expected six stress components")
                    report.components = tuple(parse_pressure(field) for field in fields)
                except ValueError as error:
                    last_block_error = f"Invalid stress at line {line_number}: {error}."
                else:
                    last_block_error = None

            if match := PRESSURE_PATTERN.search(line):
                report.external_pressure = parse_pressure(match.group(1))
            if match := PULAY_PATTERN.search(line):
                report.pulay_stress = parse_pressure(match.group(1))
            if ACCURACY_MARKER in line:
                report.accuracy_reached = True
            if "General timing and accounting" in line:
                report.normal_termination = True

    trace_only = report.isif == 1 and report.external_pressure is not None
    if last_block_error is not None and not trace_only:
        raise ValueError(last_block_error)
    if report.components is None and not trace_only:
        raise ValueError(
            "No stress tensor found. Check that OUTCAR contains stress output (ISIF >= 2)."
        )
    return report


def format_report(path: Path, report: StressReport, threshold: float | None) -> str:
    """Format stresses in GPa, keeping stress screening separate from convergence."""
    lines = [
        "========== VASP Final Cell Stress ==========",
        f"OUTCAR: {path}",
        "All stresses and pressures below are in GPa.",
        f"Stress blocks read: {report.block_count}; final stress line: {report.line_number}",
        f"ISIF: {report.isif if report.isif is not None else 'not found'}",
        f"Structural accuracy marker: {'FOUND' if report.accuracy_reached else 'NOT FOUND'}",
        f"Normal termination marker: {'FOUND' if report.normal_termination else 'NOT FOUND'}",
    ]
    for label, value in (
        ("PSTRESS", report.pstress),
        ("Printed external pressure", report.external_pressure),
        ("Printed Pulay stress", report.pulay_stress),
    ):
        if value is not None:
            lines.append(f"{label}: {value:.6f} GPa")

    if report.isif == 1:
        lines.append("ISIF=1: only the printed external pressure is reliable; tensor components are omitted.")
    elif report.components is not None:
        xx, yy, zz, xy, yz, zx = report.components
        pressure = (xx + yy + zz) / 3.0
        maximum = max(abs(value) for value in report.components)
        deviatoric = (xx - pressure, yy - pressure, zz - pressure, xy, yz, zx)
        lines.extend([
            "",
            "Final printed stress components (GPa):",
            "".join(f"{component:>12}" for component in COMPONENTS),
            "".join(f"{value:12.6f}" for value in report.components),
            "Stress tensor in Cartesian x, y, z (GPa):",
        ])
        for row in ((xx, xy, zx), (xy, yy, yz), (zx, yz, zz)):
            lines.append("  " + " ".join(f"{value:12.6f}" for value in row))
        lines.extend([
            f"Mean normal pressure, trace/3: {pressure:.6f} GPa",
            f"Maximum absolute component: {maximum:.6f} GPa",
            f"Maximum absolute shear component: {max(abs(xy), abs(yz), abs(zx)):.6f} GPa",
            f"Maximum absolute deviatoric component: {max(abs(value) for value in deviatoric):.6f} GPa",
        ])
        if threshold is not None:
            if report.isif in (3, 6) and report.pstress == 0.0:
                result = "WITHIN" if maximum <= threshold else "ABOVE"
                lines.append(f"Zero-stress screening: {result} threshold {threshold:.6f} GPa")
            else:
                lines.append(
                    f"Zero-stress screening (threshold {threshold:.6f} GPa): NOT APPLIED. "
                    "Requires ISIF=3/6 and an explicit zero PSTRESS in OUTCAR."
                )
    if report.isif in (0, 1, 2):
        lines.append("The cell was fixed by ISIF; ionic convergence does not require zero cell stress.")
    elif report.isif in (4, 5):
        lines.append("ISIF fixes the volume; hydrostatic pressure need not vanish.")
    elif report.isif in (7, 8):
        lines.append("ISIF fixes the cell shape; shear and deviatoric stresses need not vanish.")
    if report.pstress not in (None, 0.0):
        lines.append("Nonzero PSTRESS: interpret stress using the applied pressure/Pulay correction.")
    lines.extend([
        "",
        "VASP sign convention: positive normal stress is compression; negative is tension.",
        "Values are as printed by VASP; PSTRESS is not subtracted again.",
        "Stress screening alone does not establish ionic/electronic convergence.",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report the final OUTCAR cell stress and pressure in GPa."
    )
    parser.add_argument(
        "input", nargs="?", type=Path, default=Path("OUTCAR"),
        help="OUTCAR, OUTCAR.gz, or its directory (default: OUTCAR)",
    )
    parser.add_argument(
        "--threshold", type=float,
        help="Optional maximum absolute component for zero-stress screening, in GPa (no default)",
    )
    args = parser.parse_args()
    if args.threshold is not None and (
        not math.isfinite(args.threshold) or args.threshold < 0
    ):
        parser.error("--threshold must be a finite non-negative value in GPa.")
    path = args.input.expanduser().resolve()
    if path.is_dir():
        path = path / "OUTCAR"
    if not path.is_file():
        parser.error(f"OUTCAR file not found: {path}")
    try:
        report = read_stress(path)
    except (OSError, EOFError, ValueError) as error:
        parser.error(f"Cannot read stress from {path}: {error}")
    print(format_report(path, report, args.threshold))


if __name__ == "__main__":
    main()
