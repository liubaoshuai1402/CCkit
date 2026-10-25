# CCkit 功能说明：
# 比较 eos-maker 体积扫描目录中的 DFT 与 NEP 状态方程。
"""Fit and plot DFT and NEP EOS data from completed VASP volume scans."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from ase.calculators.calculator import Calculator
from ase.io import read
from pymatgen.analysis.eos import EOS


def find_eos_folders(root: Path) -> list[Path]:
    """Find eos-maker V_* folders and legacy numeric folders in volume order."""
    candidates: list[tuple[float, Path]] = []
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        name = folder.name
        if name.startswith("V_"):
            if not name[2:].isdigit():
                continue
            ratio = int(name[2:]) / 1000
        else:
            try:
                ratio = float(name)
            except ValueError:
                continue
        if np.isfinite(ratio):
            candidates.append((ratio, folder))
    return [folder for _, folder in sorted(candidates, key=lambda item: (item[0], item[1].name))]


def collect_eos_data(root: Path, calculator: Calculator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read completed scans and return volume, DFT, and NEP energy per atom."""
    folders = find_eos_folders(root)
    if not folders:
        raise ValueError(f"No V_* or numeric EOS folders found in {root}")

    volumes: list[float] = []
    dft_energies: list[float] = []
    nep_energies: list[float] = []

    for folder in folders:
        outcar = folder / "OUTCAR"
        if not outcar.is_file():
            outcar = folder / "OUTCAR.gz"
        if not outcar.is_file():
            print(f"Skip {folder.name}: OUTCAR not found")
            continue

        structure = folder / "CONTCAR"
        if not structure.is_file():
            structure = folder / "POSCAR"
        if not structure.is_file():
            print(f"Skip {folder.name}: CONTCAR/POSCAR not found")
            continue

        try:
            dft_atoms = read(outcar, index=-1)
            nep_atoms = read(structure, index=0)
            if len(dft_atoms) != len(nep_atoms) or len(nep_atoms) == 0:
                raise ValueError("OUTCAR and structure have different or zero atom counts")
            atom_count = len(nep_atoms)
            volume = float(dft_atoms.get_volume()) / atom_count
            dft_energy = float(dft_atoms.get_potential_energy()) / atom_count
            nep_atoms.calc = calculator
            nep_energy = float(nep_atoms.get_potential_energy()) / atom_count
        except (OSError, ValueError, RuntimeError) as error:
            raise ValueError(f"Could not read completed calculation in {folder}: {error}") from error

        if not np.all(np.isfinite((volume, dft_energy, nep_energy))) or volume <= 0:
            raise ValueError(f"Invalid volume or energy in {folder}")
        volumes.append(volume)
        dft_energies.append(dft_energy)
        nep_energies.append(nep_energy)

    if len(volumes) < 4 or len(set(volumes)) < 4:
        raise ValueError("At least four completed EOS folders with distinct volumes are required")

    order = np.argsort(volumes)
    return (
        np.asarray(volumes)[order],
        np.asarray(dft_energies)[order],
        np.asarray(nep_energies)[order],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare DFT and NEP EOS curves from volume scans.")
    parser.add_argument("--eos", type=Path, default=Path("."), help="EOS root with V_* or numeric folders")
    parser.add_argument("--nep", type=Path, default=Path("nep.txt"), help="NEP potential file")
    parser.add_argument("--out", default="EOS_DFT_vs_NEP", help="Output base path for .txt and .png")
    args = parser.parse_args()

    root = args.eos.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"EOS directory does not exist: {root}")
    if not args.nep.is_file():
        parser.error(f"NEP potential does not exist: {args.nep}")

    try:
        from calorine.calculators import CPUNEP
    except ImportError:
        parser.error("calorine is required for NEP energy calculations")

    try:
        calculator = CPUNEP(str(args.nep))
        volumes, dft_energies, nep_energies = collect_eos_data(root, calculator)
        fit_dft = EOS(eos_name="birch_murnaghan").fit(volumes, dft_energies)
        fit_nep = EOS(eos_name="birch_murnaghan").fit(volumes, nep_energies)
    except ValueError as error:
        parser.error(str(error))

    print(
        f"DFT: V0={fit_dft.v0:.4f} A3/atom, "
        f"B0={fit_dft.b0 * 160.2177:.2f} GPa, "
        f"E0={fit_dft.e0:.6f} eV/atom"
    )
    print(
        f"NEP: V0={fit_nep.v0:.4f} A3/atom, "
        f"B0={fit_nep.b0 * 160.2177:.2f} GPa, "
        f"E0={fit_nep.e0:.6f} eV/atom"
    )

    curve_volumes = np.linspace(volumes.min(), volumes.max(), 200)
    plt.figure(figsize=(5, 4))
    plt.scatter(volumes, dft_energies, label="DFT")
    plt.scatter(volumes, nep_energies, label="NEP")
    plt.plot(curve_volumes, fit_dft(curve_volumes), label="DFT EOS")
    plt.plot(curve_volumes, fit_nep(curve_volumes), "--", label="NEP EOS")
    plt.xlabel(r"Volume ($\AA^3$/atom)")
    plt.ylabel("Energy (eV/atom)")
    plt.legend()
    plt.tight_layout()

    output_base = Path(args.out)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    plot_path = output_base.with_name(output_base.name + ".png")
    data_path = output_base.with_name(output_base.name + ".txt")
    plt.savefig(plot_path, dpi=600)
    plt.close()
    np.savetxt(
        data_path,
        np.column_stack((volumes, dft_energies, nep_energies)),
        header="Volume(A3/atom) DFT(eV/atom) NEP(eV/atom)",
        fmt="%.8f",
    )
    print(f"Used {len(volumes)} completed EOS calculations")
    print(f"Saved: {data_path.resolve()}")
    print(f"Saved: {plot_path.resolve()}")


if __name__ == "__main__":
    main()
