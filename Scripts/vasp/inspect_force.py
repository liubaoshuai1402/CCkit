# CCkit 功能说明：读取 OUTCAR 已完成离子步的最大原子受力，绘制分量及合力曲线，可定时刷新。
"""Plot maximum atomic forces per ionic step from an OUTCAR, including live runs.

ASE parses atom counts and force tables. A small framing layer withholds partial
EOF records and waits for the ionic summary, as in ASE's OUTCAR chunk reader.
This avoids parsing unrelated properties or a partly written nearby CONTCAR.
Raw forces include fixed atoms; no constraints are applied to the values.
"""

from __future__ import annotations

import argparse
import gzip
import math
import time
from collections.abc import Generator
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
import numpy as np

if TYPE_CHECKING:
    from matplotlib.figure import Figure


ForceMaxima = tuple[float, float, float, float]
COMPONENTS = ("x", "y", "z", "total")
FORCE_LABELS = (r"max $|F_x|$", r"max $|F_y|$", r"max $|F_z|$", r"max $|\mathbf{F}|$")
COLORS = ("#3267c8", "#d77a30", "#8864b5", "#138b80")


def complete_lines(path: Path) -> Generator[str, None, None]:
    """Stream complete lines, excluding a partly written EOF line."""
    open_file = gzip.open if path.suffix.lower() == ".gz" else Path.open
    with open_file(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.endswith("\n"):
                break
            yield line


def summarize_forces(forces: np.ndarray) -> ForceMaxima:
    """Return max |Fx|, |Fy|, |Fz|, and max atomic vector norm in eV/Angstrom.

    Each maximum is taken independently over all atoms. The total is the
    largest norm of an individual atom's force, not a norm of component maxima.
    """
    if forces.ndim != 2 or forces.shape[1] != 3 or len(forces) == 0:
        raise ValueError("Expected a non-empty array of atomic forces with shape (N, 3).")
    if not np.isfinite(forces).all():
        raise ValueError("An atomic force is NaN or infinite; check the OUTCAR.")
    component_maxima = np.abs(forces).max(axis=0)
    total_maximum = float(np.linalg.norm(forces, axis=1).max())
    if not math.isfinite(total_maximum):
        raise ValueError("Atomic force magnitudes overflow; check the OUTCAR.")
    return (
        float(component_maxima[0]), float(component_maxima[1]),
        float(component_maxima[2]), total_maximum,
    )


def read_force_maxima(path: Path) -> list[ForceMaxima]:
    """Stream complete ionic force records via ASE; ignore an unfinished last step.

    Only atom-count and force-table numbers are parsed. ASE's Energy delimiter
    and five-line summary boundary define completion of the ionic step, keeping
    step numbering consistent with inspect-energy for the same OUTCAR.
    """
    from ase.io.vasp_parsers.vasp_outcar_parsers import Energy, IonsPerSpecies, PositionsAndForces

    count_parser = IonsPerSpecies()
    force_parser = PositionsAndForces()
    energy_parser = Energy()
    atom_count = None
    pending = None
    records = []
    lines = complete_lines(path)
    try:
        for line in lines:
            if count_parser.has_property(0, [line]):
                counts = count_parser.parse(0, [line])["ion_types"]
                if not counts or any(count < 0 for count in counts) or sum(counts) == 0:
                    raise ValueError("Invalid atom counts in 'ions per type'.")
                atom_count = sum(counts)
                force_parser.header = {"natoms": atom_count}
                pending = None
            elif force_parser.has_property(0, [line]):
                if atom_count is None:
                    raise ValueError("Force table found before 'ions per type'; supply a full OUTCAR.")
                # Header, separator, N atomic rows, and a closing separator.
                block = [line, *islice(lines, atom_count + 2)]
                if len(block) < atom_count + 3:
                    break
                if set(block[-1].strip()) != {"-"}:
                    raise ValueError(f"Missing closing separator in force table {len(records) + 1}.")
                try:
                    forces = force_parser.parse(0, block)["forces"]
                    pending = summarize_forces(forces)
                except (IndexError, ValueError) as error:
                    raise ValueError(f"Invalid force table for ionic step {len(records) + 1}: {error}") from error
            elif energy_parser.has_property(0, [line]):
                if len(list(islice(lines, 4))) < 4:
                    break
                if pending is None:
                    raise ValueError(f"No force table found for completed ionic step {len(records) + 1}.")
                records.append(pending)
                pending = None
    finally:
        lines.close()
    return records


def resolve_input(path: Path) -> Path:
    """Accept an OUTCAR filename (including renamed files or .gz) or directory."""
    path = path.expanduser().resolve()
    if path.is_dir():
        candidates = (path / "OUTCAR", path / "OUTCAR.gz")
        path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not path.is_file():
        raise ValueError(f"OUTCAR file not found: {path}")
    return path


def resolve_output(path: Path, input_path: Path) -> Path:
    """Keep default and bare output filenames beside the input file."""
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


def draw_forces(figure: Figure, records: list[ForceMaxima], component: str) -> None:
    """Plot selected force maxima in eV/Angstrom against completed ionic steps."""
    from matplotlib.ticker import MaxNLocator

    figure.clear()
    figure.set_facecolor("#f4f7fb")
    axis = figure.subplots()
    axis.set_facecolor("white")
    axis.spines[["top", "right"]].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color("#d4dce8")
    axis.tick_params(axis="both", which="both", direction="in", colors="#506078", labelsize=10)
    axis.grid(axis="y", color="#e7ecf3", linewidth=0.8)
    axis.set_axisbelow(True)

    steps = np.arange(1, len(records) + 1)
    values = np.asarray(records)
    for index, name in enumerate(COMPONENTS):
        if component != "all" and component != name:
            continue
        axis.plot(
            steps, values[:, index], color=COLORS[index],
            linewidth=2.3 if name == "total" else 1.6,
            linestyle="-" if name == "total" else ("--", "-.", ":")[index],
            marker="o" if len(records) <= 100 else None, markersize=3,
            label=f"{FORCE_LABELS[index]}  =  {values[-1, index]:.5g}",
        )
        axis.scatter(
            steps[-1], values[-1, index], s=45, color=COLORS[index],
            edgecolor="white", linewidth=0.8, zorder=4,
        )
    axis.set_xlabel("Ionic step (completed records, starting at 1)", color="#27364d", labelpad=8)
    axis.set_ylabel(r"Maximum atomic force (eV/$\mathrm{\AA}$)", color="#27364d", labelpad=10)
    axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=9))
    axis.yaxis.set_major_locator(MaxNLocator(nbins=6))
    axis.set_xlim(0.6, max(1.4, len(records) + 0.4))
    axis.set_ylim(bottom=0)
    axis.legend(
        title=r"Latest maxima (eV/$\mathrm{\AA}$)", loc="upper right",
        frameon=True, facecolor="white", edgecolor="#e7ecf3", labelcolor="#27364d",
    )
    for label in axis.get_xticklabels(which="both") + axis.get_yticklabels(which="both"):
        label.set_fontweight("bold")
    axis.xaxis.get_offset_text().set_fontweight("bold")
    axis.yaxis.get_offset_text().set_fontweight("bold")
    figure.suptitle(
        "Force",
        fontsize=14, fontweight="normal", color="#1e2d44",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot maximum atomic forces at completed OUTCAR ionic steps, including live runs."
    )
    parser.add_argument(
        "input", nargs="?", type=Path, default=Path("OUTCAR"),
        help="OUTCAR, OUTCAR.gz, or its directory (default: OUTCAR); renamed OUTCAR files are accepted",
    )
    parser.add_argument(
        "--component", choices=("all", *COMPONENTS), default="all",
        help="all: four curves; x/y/z: max absolute component; total: max atomic vector norm (default: all)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("force_vs_step.png"),
        help="PNG/PDF/SVG path; default and bare filenames go beside input (default: force_vs_step.png)",
    )
    parser.add_argument(
        "--watch", nargs="?", const=5.0, type=float, metavar="SECONDS",
        help="Refresh until Ctrl+C; optional positive interval in seconds (default when given: 5)",
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Also open a GUI window; closing it with --watch stops monitoring (requires a GUI backend)",
    )
    args = parser.parse_args()
    if args.watch is not None and (not math.isfinite(args.watch) or args.watch <= 0):
        parser.error("--watch must be a finite positive interval in seconds.")
    try:
        input_path = resolve_input(args.input)
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
            records = read_force_maxima(input_path)
            if records != previous:
                if records:
                    if figure is None:
                        figure = plt.figure(figsize=(9.5, 5.8), constrained_layout=True)
                    draw_forces(figure, records, args.component)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    figure.savefig(output_path, dpi=600, facecolor=figure.get_facecolor())
                    latest = records[-1]
                    print(
                        f"{len(records)} completed ionic steps; latest maxima (eV/Angstrom): "
                        f"|Fx|={latest[0]:.6g}, |Fy|={latest[1]:.6g}, |Fz|={latest[2]:.6g}, |F|={latest[3]:.6g}\n"
                        f"Plot: {output_path}", flush=True,
                    )
                    if args.show:
                        plt.show(block=False)
                elif args.watch is None:
                    parser.error(f"No completed ionic force records found in {input_path}.")
                else:
                    print(
                        "Waiting for a completed ionic force record."
                        + (" Existing plot retains the previous snapshot." if figure is not None else ""),
                        flush=True,
                    )
                previous = records
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
        parser.error(f"Cannot inspect forces in {input_path}: {error}")
    finally:
        if figure is not None:
            plt.close(figure)


if __name__ == "__main__":
    main()
