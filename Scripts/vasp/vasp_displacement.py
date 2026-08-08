# CCkit 功能说明：
# 比较 POSCAR 与 CONTCAR，统计结构优化前后每个原子的位移并输出位移最大的原子。
import argparse
from pathlib import Path

import numpy as np
from ase.geometry import find_mic
from ase.io import read


def validate_structures(reference, relaxed):
    """Ensure POSCAR and CONTCAR describe the same ordered atoms."""
    if len(reference) != len(relaxed):
        raise ValueError(
            "POSCAR and CONTCAR must contain the same number of atoms."
        )

    reference_symbols = reference.get_chemical_symbols()
    relaxed_symbols = relaxed.get_chemical_symbols()
    if reference_symbols != relaxed_symbols:
        raise ValueError(
            "POSCAR and CONTCAR must have identical element order."
        )


def calculate_displacements(reference, relaxed):
    """Return per-atom displacement magnitudes using POSCAR minimum images."""
    validate_structures(reference, relaxed)
    displacement_vectors = relaxed.positions - reference.positions
    _, displacement_magnitudes = find_mic(
        displacement_vectors,
        reference.cell,
        pbc=reference.pbc,
    )
    return displacement_magnitudes


def print_summary(poscar_path, contcar_path, symbols, displacements, top_count):
    """Print the requested largest displacements and total displacement."""
    ranked_indices = np.argsort(displacements)[::-1]
    displayed_indices = ranked_indices[:top_count]

    print("========== VASP Atomic Displacement ==========")
    print(f"POSCAR  : {poscar_path}")
    print(f"CONTCAR : {contcar_path}")
    print(f"Total displacement: {displacements.sum():.6f} Angstrom")
    print()
    print(
        f"Top {len(displayed_indices)} atoms by displacement "
        "(0-based index):"
    )
    print(f"{'Rank':>4}  {'Element':<7}  {'Index':>5}  {'Displacement (Angstrom)':>24}")
    for rank, atom_index in enumerate(displayed_indices, start=1):
        print(
            f"{rank:>4}  {symbols[atom_index]:<7}  {atom_index:>5}  "
            f"{displacements[atom_index]:>24.6f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare POSCAR and CONTCAR atomic displacements after relaxation."
        )
    )
    parser.add_argument(
        "poscar",
        nargs="?",
        default="POSCAR",
        help="Initial VASP structure (default: POSCAR)",
    )
    parser.add_argument(
        "contcar",
        nargs="?",
        default="CONTCAR",
        help="Relaxed VASP structure (default: CONTCAR)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=10,
        help="Number of atoms with the largest displacement to show (default: 10)",
    )
    args = parser.parse_args()

    if args.top < 1:
        parser.error("--top must be a positive integer.")

    poscar_path = Path(args.poscar)
    contcar_path = Path(args.contcar)
    for path in (poscar_path, contcar_path):
        if not path.is_file():
            parser.error(f"Structure file does not exist: {path}")

    reference = read(poscar_path)
    relaxed = read(contcar_path)
    try:
        displacements = calculate_displacements(reference, relaxed)
    except ValueError as error:
        parser.error(str(error))

    print_summary(
        poscar_path,
        contcar_path,
        reference.get_chemical_symbols(),
        displacements,
        args.top,
    )


if __name__ == "__main__":
    main()
