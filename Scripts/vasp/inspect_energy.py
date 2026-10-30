# CCkit 功能说明：读取 VASP 已完成离子步的能量，绘制能量及步间变化曲线，可定时刷新。
"""Inspect ionic relaxation energies from OSZICAR or OUTCAR, including live runs.

pymatgen parses OSZICAR summaries; ASE parses OUTCAR ionic energy blocks.
Only newline-terminated records are passed to those parsers. The small framing
layer is needed because their full-file readers do not uniformly tolerate a
partly written last record. No electronic iteration energies are collected.
"""

from __future__ import annotations

import argparse
import gzip
import math
import re
import tempfile
import time
from collections.abc import Generator
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
import numpy as np

if TYPE_CHECKING:
    from matplotlib.figure import Figure


IONIC_SUMMARY = re.compile(r"^\s*\d+\s+F=")
ENERGY_LABELS = {"F": "Free energy F / TOTEN", "E0": "Energy E0 / sigma -> 0"}


def complete_lines(path: Path) -> Generator[str, None, None]:
    """Stream complete text lines, leaving an unfinished EOF line for next time."""
    open_file = gzip.open if path.suffix.lower() == ".gz" else Path.open
    with open_file(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.endswith("\n"):
                break
            yield line


def read_oszicar(path: Path, energy: str) -> list[float]:
    """Return one energy in eV per complete OSZICAR ionic summary, in file order."""
    from pymatgen.io.vasp.outputs import Oszicar

    # Oszicar accepts filenames only. Isolate complete ionic summaries so that
    # unfinished electronic rows cannot abort parsing of earlier ionic steps.
    with tempfile.TemporaryDirectory(prefix="cckit-inspect-energy-") as directory:
        snapshot = Path(directory) / "OSZICAR"
        with snapshot.open("w", encoding="utf-8") as handle:
            for line in complete_lines(path):
                if IONIC_SUMMARY.match(line):
                    handle.write(line)
        ionic_steps = Oszicar(snapshot).ionic_steps

    energies = []
    for index, step in enumerate(ionic_steps, start=1):
        if "F" not in step or "E0" not in step:
            raise ValueError(f"Ionic summary {index} is missing F or E0.")
        energies.append(float(step[energy]))
    return energies


def read_outcar(path: Path, energy: str) -> list[float]:
    """Return ionic energies in eV using ASE's five-line energy-block parser.

    Energy locates VASP's final ionic summary, rather than the energy printed
    during each electronic iteration. Framing only that block avoids requiring
    positions, k-points, or a readable neighbouring CONTCAR during a live run.
    """
    from ase.io.vasp_parsers.vasp_outcar_parsers import Energy

    energy_parser = Energy()
    key = "free_energy" if energy == "F" else "energy"
    energies = []
    lines = complete_lines(path)
    try:
        for line in lines:
            if not energy_parser.has_property(0, [line]):
                continue
            block = [line, *islice(lines, 4)]
            if len(block) < 5:
                break  # The current ionic energy summary is still being written.
            try:
                values = energy_parser.parse(0, block)
            except (IndexError, ValueError) as error:
                raise ValueError(
                    f"Invalid completed ionic energy block {len(energies) + 1}: {error}"
                ) from error
            energies.append(float(values[key]))
    finally:
        lines.close()
    return energies


def read_energies(path: Path, source: str, energy: str) -> list[float]:
    """Read finite ionic energies in eV without requiring normal termination."""
    values = read_oszicar(path, energy) if source == "oszicar" else read_outcar(path, energy)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("An ionic energy is NaN or infinite; check the calculation output.")
    return values


def resolve_input(path: Path, source: str) -> tuple[Path, str]:
    """Resolve a file or choose OSZICAR before OUTCAR inside a calculation folder."""
    path = path.expanduser().resolve()
    if path.is_dir():
        names = ("OSZICAR", "OUTCAR") if source == "auto" else (source.upper(),)
        candidates = [path / (name + suffix) for name in names for suffix in ("", ".gz")]
        path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not path.is_file():
        raise ValueError(f"Input file not found: {path}")
    if source == "auto":
        name = path.name.upper().removesuffix(".GZ")
        if name not in {"OSZICAR", "OUTCAR"}:
            raise ValueError("For a renamed input, specify --format oszicar or --format outcar.")
        source = name.lower()
    return path, source


def resolve_output(path: Path, input_path: Path) -> Path:
    """Put a bare output filename beside the input; honour explicit directories."""
    path = path.expanduser()
    if not path.is_absolute() and path.parent == Path("."):
        path = input_path.parent / path
    if not path.suffix:
        path = path.with_suffix(".png")
    path = path.resolve()
    if path == input_path:
        raise ValueError("The plot output must differ from the input file.")
    if path.suffix.lower() not in {".png", ".pdf", ".svg"}:
        raise ValueError("Plot output must use .png, .pdf, or .svg.")
    return path


def draw_energy(figure: Figure, energies: list[float], energy: str) -> None:
    """Draw total energy and signed adjacent-step changes in eV on ionic axes."""
    from matplotlib.ticker import FormatStrFormatter, MaxNLocator, ScalarFormatter

    figure.clear()
    figure.set_facecolor("#f4f7fb")
    axes = figure.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    energy_axis, delta_axis = axes
    steps = np.arange(1, len(energies) + 1)
    values = np.asarray(energies)
    deltas = np.diff(values)
    blue, teal, orange = "#3267c8", "#138b80", "#d77a30"

    for axis in axes:
        axis.set_facecolor("white")
        axis.spines[["top", "right"]].set_visible(False)
        for side in ("left", "bottom"):
            axis.spines[side].set_color("#d4dce8")
        axis.tick_params(axis="both", which="both", direction="in", colors="#506078", labelsize=10)
        axis.grid(axis="y", color="#e7ecf3", linewidth=0.8)
        axis.set_axisbelow(True)

    energy_axis.plot(
        steps, values, color=blue, linewidth=1.9,
        marker="o" if len(values) <= 100 else None, markersize=3.5,
    )
    energy_axis.scatter(steps[-1], values[-1], s=55, color=teal, edgecolor="white", zorder=4)
    energy_axis.set_ylabel(f"{ENERGY_LABELS[energy]} (eV)", color="#27364d", labelpad=10)
    formatter = ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    energy_axis.yaxis.set_major_formatter(formatter)
    energy_axis.yaxis.set_major_locator(MaxNLocator(nbins=6))
    energy_axis.text(
        0.98, 0.96, f"Latest: {values[-1]:.6f} eV", transform=energy_axis.transAxes,
        ha="right", va="top", fontsize=11, color=teal,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#edf7f5", "edgecolor": "none"},
    )
    delta_axis.axhline(0, color="#9eacbe", linewidth=0.9, linestyle="--")
    if deltas.size:
        delta_axis.plot(steps[1:], deltas, color="#94a6bd", linewidth=1.1)
        delta_axis.scatter(steps[1:], deltas, c=np.where(deltas > 0, orange, teal), s=17, zorder=3)
        delta_axis.text(
            0.98, 0.94, f"Latest change: {deltas[-1]:+.3e} eV",
            transform=delta_axis.transAxes, ha="right", va="top", fontsize=10, color="#506078",
        )
    else:
        delta_axis.text(
            0.5, 0.5, "Step changes appear after the second ionic step",
            transform=delta_axis.transAxes, ha="center", va="center", color="#506078",
        )
    delta_axis.set_ylabel("Step change (eV)", color="#27364d")
    delta_axis.set_yscale("linear")
    delta_axis.yaxis.set_major_formatter(FormatStrFormatter("%.1e"))
    delta_axis.yaxis.set_major_locator(MaxNLocator(nbins=4))
    delta_axis.set_xlabel("Ionic step (completed records, starting at 1)", color="#27364d", labelpad=8)
    delta_axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=9))
    delta_axis.set_xlim(0.6, max(1.4, len(values) + 0.4))
    for axis in axes:
        for label in axis.get_xticklabels(which="both") + axis.get_yticklabels(which="both"):
            label.set_fontweight("bold")
        axis.xaxis.get_offset_text().set_fontweight("bold")
        axis.yaxis.get_offset_text().set_fontweight("bold")
    figure.suptitle(
        "Energy",
        fontsize=14, fontweight="normal", color="#1e2d44",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot completed VASP ionic-step energies; ignore electronic iterations and unfinished EOF records."
    )
    parser.add_argument(
        "input", nargs="?", type=Path, default=Path("."),
        help="OSZICAR, OUTCAR (also .gz), or a directory; default: current directory, preferring OSZICAR",
    )
    parser.add_argument(
        "--format", choices=("auto", "oszicar", "outcar"), default="auto",
        help="Input format, useful for renamed files (default: infer from filename)",
    )
    parser.add_argument(
        "--energy", choices=("F", "E0"), default="F",
        help="F: free energy / TOTEN; E0: sigma->0 energy, both in eV per cell (default: F)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("energy_vs_step.png"),
        help="PNG/PDF/SVG path; default and bare filenames go beside input (default: energy_vs_step.png)",
    )
    parser.add_argument(
        "--watch", nargs="?", const=5.0, type=float, metavar="SECONDS",
        help="Refresh until Ctrl+C; optional positive interval in seconds (default when given: 5)",
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Also open a plot window; with --watch, closing the window stops monitoring (requires a GUI backend)",
    )
    args = parser.parse_args()
    if args.watch is not None and (not math.isfinite(args.watch) or args.watch <= 0):
        parser.error("--watch must be a finite positive interval in seconds.")
    try:
        input_path, source = resolve_input(args.input, args.format)
        output_path = resolve_output(args.output, input_path)
    except ValueError as error:
        parser.error(str(error))

    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = None
    previous = None
    try:
        while True:
            energies = read_energies(input_path, source, args.energy)
            if energies != previous:
                if energies:
                    if figure is None:
                        figure = plt.figure(figsize=(9.5, 6.5), constrained_layout=True)
                    draw_energy(figure, energies, args.energy)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    figure.savefig(output_path, dpi=220, facecolor=figure.get_facecolor())
                    change = f"; last dE = {energies[-1] - energies[-2]:+.6g} eV" if len(energies) > 1 else ""
                    print(
                        f"{len(energies)} completed ionic steps; latest {args.energy} = {energies[-1]:.8f} eV{change}\n"
                        f"Plot: {output_path}", flush=True,
                    )
                    if args.show:
                        plt.show(block=False)
                elif args.watch is None:
                    parser.error(f"No completed ionic energy records found in {input_path}.")
                else:
                    print(
                        "Waiting for a completed ionic energy record."
                        + (" Existing plot retains the previous snapshot." if figure is not None else ""),
                        flush=True,
                    )
                previous = energies
            if args.watch is None:
                if args.show:
                    plt.show()
                break
            deadline = time.monotonic() + args.watch
            if args.show and figure is not None:
                while time.monotonic() < deadline:
                    if not plt.fignum_exists(figure.number):
                        return
                    plt.pause(min(0.2, max(0.001, deadline - time.monotonic())))
            else:
                time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nMonitoring stopped." + (" The last saved plot is retained." if figure is not None else ""))
    except (OSError, EOFError, ValueError, IndexError, ImportError) as error:
        parser.error(f"Cannot inspect {input_path}: {error}")
    finally:
        if figure is not None:
            plt.close(figure)


if __name__ == "__main__":
    main()
