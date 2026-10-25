# CCkit 功能说明：生成定体积 VASP 计算目录并拟合能量-体积状态方程。
"""Prepare EOS volume-scan structures or fit completed VASP calculations.

The ``make`` operation creates isotropically scaled structures beside the
input structure. The ``fit`` operation reads OUTCAR files from ``V_*``
subdirectories and writes Birch-Murnaghan fit data and a plot to that directory.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def volume_directory_name(scale: float) -> str:
    """Return the V_* folder name used by the reference EOS workflow."""
    return f"V_{int(round(scale * 1000))}"


def make_volume_scan(
    structure_path: Path,
    incar_path: Path,
    potcar_path: Path,
    start: float,
    stop: float,
    points: int,
    overwrite: bool,
) -> list[tuple[Path, float]]:
    """Write isotropically scaled POSCARs and copy VASP input files.

    ``start`` and ``stop`` are volume ratios. Scaling the cell vectors by the
    cube root of each ratio while scaling positions preserves fractional
    coordinates.
    """
    import numpy as np
    from ase.io import read, write

    atoms = read(structure_path, index=0)
    cell = atoms.cell.copy()
    scales = np.linspace(start, stop, points)
    names = [volume_directory_name(float(scale)) for scale in scales]
    if len(set(names)) != len(names):
        raise ValueError("Volume ratios produce duplicate V_* directory names.")

    output_directories = [structure_path.parent / name for name in names]
    existing = [directory for directory in output_directories if directory.exists()]
    if existing and not overwrite:
        paths = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            f"Output directories already exist: {paths}. Use --overwrite to replace EOS input files."
        )

    created: list[tuple[Path, float]] = []
    for scale, directory in zip(scales, output_directories):
        directory.mkdir(parents=True, exist_ok=True)
        scaled_atoms = atoms.copy()
        scaled_atoms.set_cell(cell * float(scale) ** (1.0 / 3.0), scale_atoms=True)
        write(directory / "POSCAR", scaled_atoms, format="vasp", direct=True, vasp5=True)
        shutil.copy2(incar_path, directory / "INCAR")
        shutil.copy2(potcar_path, directory / "POTCAR")
        created.append((directory, float(scaled_atoms.get_volume())))
    return created


def collect_eos_data(directory: Path) -> tuple[np.ndarray, np.ndarray, list[Path]]:
    """Collect volume and final energy from OUTCAR files in V_* directories."""
    import numpy as np
    from ase.io import read

    volumes: list[float] = []
    energies: list[float] = []
    sources: list[Path] = []
    for subdirectory in sorted(directory.glob("V_*")):
        if not subdirectory.is_dir():
            continue
        outcar_path = subdirectory / "OUTCAR"
        if not outcar_path.is_file():
            print(f"Skip {subdirectory.name}: OUTCAR not found")
            continue
        try:
            atoms = read(outcar_path, index=-1)
            volume = float(atoms.get_volume())
            energy = float(atoms.get_potential_energy())
        except Exception as exc:
            raise ValueError(f"Could not read completed calculation {outcar_path}: {exc}") from exc
        if not np.isfinite(volume) or volume <= 0 or not np.isfinite(energy):
            raise ValueError(f"OUTCAR contains invalid volume or energy: {outcar_path}")
        volumes.append(volume)
        energies.append(energy)
        sources.append(outcar_path)

    if len(volumes) < 4:
        raise ValueError(
            f"Need at least four valid V_* / OUTCAR calculations for EOS fitting; found {len(volumes)}."
        )
    volume_array = np.asarray(volumes)
    energy_array = np.asarray(energies)
    order = np.argsort(volume_array)
    return volume_array[order], energy_array[order], [sources[i] for i in order]


def fit_eos(directory: Path, dpi: int, energy_offset: bool) -> None:
    """Fit Birch-Murnaghan EOS and save data, parameters, and a figure."""
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    from pymatgen.analysis.eos import EOS

    volumes, energies, sources = collect_eos_data(directory)
    if len(np.unique(volumes)) < 4:
        raise ValueError("EOS fitting requires at least four distinct volumes.")

    fit = EOS("birch_murnaghan").fit(volumes, energies)
    data_path = directory / "EOS.dat"
    parameters_path = directory / "EOS_fit.txt"
    curve_path = directory / "EOS_fit_curve.dat"
    plot_path = directory / "EOS.png"

    np.savetxt(
        data_path,
        np.column_stack((volumes, energies)),
        header="Volume(Ang^3)    Energy(eV)",
        fmt="%.8f",
    )
    parameters_path.write_text(
        "Birch-Murnaghan EOS fitting\n\n"
        f"V0  = {fit.v0:.6f} Å^3\n"
        f"E0  = {fit.e0:.8f} eV\n"
        f"B0  = {fit.b0_GPa:.4f} GPa\n"
        f"B0' = {fit.b1:.6f}\n",
        encoding="utf-8",
    )

    fit_volumes = np.linspace(float(volumes.min()), float(volumes.max()), 400)
    fit_energies = np.asarray(fit.func(fit_volumes))
    np.savetxt(
        curve_path,
        np.column_stack((fit_volumes, fit_energies)),
        header="Volume(Ang^3)    Energy_fit(eV)",
        fmt="%.8f",
    )

    offset = float(np.rint(energies.min())) if energy_offset else 0.0
    ylabel = f"E {'+' if offset < 0 else '-'} {abs(offset):.1f} (eV)" if energy_offset else "Energy (eV)"
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "font.size": 11,
            "axes.linewidth": 1.1,
            "mathtext.fontset": "dejavusans",
        }
    )
    figure, axis = plt.subplots(figsize=(6.0, 4.6))
    plotted_energies = energies - offset
    plotted_fit = fit_energies - offset
    axis.scatter(volumes, plotted_energies, s=65, color="#D62728", edgecolors="white", label="DFT", zorder=3)
    axis.plot(fit_volumes, plotted_fit, color="#111111", lw=2.2, label="Birch-Murnaghan fit")
    axis.scatter(fit.v0, fit.e0 - offset, s=210, color="#1F77B4", marker="*", label="Minimum", zorder=4)
    axis.set_xlabel(r"Volume ($\mathrm{\AA^3}$)", fontsize=14)
    axis.set_ylabel(ylabel, fontsize=14)
    axis.tick_params(direction="in", top=True, right=True)
    axis.grid(True, which="major", ls="--", lw=0.6, alpha=0.35)
    axis.legend(loc="best", frameon=False)
    axis.text(
        0.03,
        0.03,
        f"$V_0$ = {fit.v0:.2f} Å³\n$E_0$ = {fit.e0:.4f} eV\n"
        f"$B_0$ = {fit.b0_GPa:.1f} GPa\n$B_0'$ = {fit.b1:.2f}",
        transform=axis.transAxes,
        fontsize=9,
        va="bottom",
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#888888", "alpha": 0.9},
    )
    figure.tight_layout()
    figure.savefig(plot_path, dpi=dpi)
    if matplotlib.get_backend().lower() != "agg":
        plt.show()
    plt.close(figure)

    print("Birch-Murnaghan EOS fitting")
    print(f"Equilibrium volume (V0): {fit.v0:.6f} A^3")
    print(f"Minimum energy (E0): {fit.e0:.8f} eV")
    print(f"Bulk modulus (B0): {fit.b0_GPa:.2f} GPa")
    print(f"B0': {fit.b1:.4f}")
    print(f"Used {len(sources)} OUTCAR files.")
    for output_path in (data_path, parameters_path, curve_path, plot_path):
        print(f"Wrote {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create VASP volume-scan jobs and fit a Birch-Murnaghan EOS."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)

    make_parser = subparsers.add_parser("make", help="Create volume-scaled VASP calculation folders")
    make_parser.add_argument("input", type=Path, help="Optimized input structure, usually CONTCAR")
    make_parser.add_argument(
        "--start", type=float, default=0.97, help="Starting volume ratio (default: 0.97)"
    )
    make_parser.add_argument(
        "--stop", type=float, default=1.02, help="Ending volume ratio (default: 1.02)"
    )
    make_parser.add_argument("--points", type=int, default=11, help="Number of volume points (default: 11)")
    make_parser.add_argument(
        "--incar", type=Path, help="INCAR source (default: INCAR-2 beside the input structure)"
    )
    make_parser.add_argument(
        "--potcar", type=Path, help="POTCAR source (default: POTCAR beside the input structure)"
    )
    make_parser.add_argument(
        "--overwrite", action="store_true", help="Replace POSCAR, INCAR, and POTCAR in existing V_* folders"
    )

    fit_parser = subparsers.add_parser("fit", help="Fit completed V_* calculations in a directory")
    fit_parser.add_argument("directory", type=Path, help="Directory containing V_*/OUTCAR calculations")
    fit_parser.add_argument("--dpi", type=int, default=600, help="EOS.png resolution (default: 600 dpi)")
    fit_parser.add_argument(
        "--energy-offset", action="store_true", help="Shift plot energies by the nearest integer baseline"
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.operation == "make":
            structure_path = args.input.expanduser().resolve()
            if not structure_path.is_file():
                parser.error(f"Input structure not found: {structure_path}")
            if not 0 < args.start <= args.stop or args.points < 4:
                parser.error("Require 0 < --start <= --stop and at least four --points.")
            incar_path = (args.incar or structure_path.parent / "INCAR-2").expanduser().resolve()
            potcar_path = (args.potcar or structure_path.parent / "POTCAR").expanduser().resolve()
            for source_path in (incar_path, potcar_path):
                if not source_path.is_file():
                    parser.error(f"Required VASP input file not found: {source_path}")
            created = make_volume_scan(
                structure_path,
                incar_path,
                potcar_path,
                args.start,
                args.stop,
                args.points,
                args.overwrite,
            )
            for output_directory, volume in created:
                print(f"{output_directory.name}: volume = {volume:.3f} A^3; wrote {output_directory}")
        else:
            directory = args.directory.expanduser().resolve()
            if not directory.is_dir():
                parser.error(f"EOS directory not found: {directory}")
            if args.dpi <= 0:
                parser.error("--dpi must be a positive integer.")
            fit_eos(directory, args.dpi, args.energy_offset)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
