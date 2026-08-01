"""Locate oxygen-vacancy coordinates in a defective structure.

By default, the script maps the reference oxygen density into the current cell,
subtracts the current oxygen density, and reports the strongest density deficits.
The resulting coordinates belong to the current (defective) structure.
"""

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from ase import Atoms
from ase.geometry import find_mic
from ase.io import read, write
from scipy.optimize import linear_sum_assignment


_WORKER_REFERENCE = None
_WORKER_ARGUMENTS = None
_WORKER_REFERENCE_COUNT = None


def element_positions(atoms, element):
    """Return Cartesian positions of one element, plus its wrapped fractions."""
    symbols = np.asarray(atoms.get_chemical_symbols())
    indices = np.flatnonzero(symbols == element)
    return atoms.positions[indices], atoms.get_scaled_positions(wrap=True)[indices]


def mic_distances(first, second, cell, pbc):
    """Pairwise minimum-image distances from ``first`` to ``second``."""
    vectors = second[None, :, :] - first[:, None, :]
    _, distances = find_mic(vectors.reshape(-1, 3), cell, pbc=pbc)
    return distances.reshape(len(first), len(second))


def wigner_seitz_vacancies(reference, structure, element, tolerance):
    """Find unoccupied reference sites using periodic one-to-one assignment."""
    ref_positions, ref_fractional = element_positions(reference, element)
    _, actual_fractional = element_positions(structure, element)

    if len(ref_positions) == 0:
        raise ValueError(f"Reference structure contains no {element!r} atoms")

    # Fractional coordinates make uniform cell expansion/contraction an affine map.
    actual_in_reference_cell = actual_fractional @ reference.cell.array
    occupied = np.zeros(len(ref_positions), dtype=bool)
    matched_distance = np.full(len(ref_positions), np.nan)

    if len(actual_in_reference_cell):
        distances = mic_distances(
            ref_positions, actual_in_reference_cell, reference.cell, reference.pbc
        )
        reference_indices, actual_indices = linear_sum_assignment(distances)
        assigned_distances = distances[reference_indices, actual_indices]
        matched_distance[reference_indices] = assigned_distances
        occupied[reference_indices] = assigned_distances <= tolerance

    vacancy_indices = np.flatnonzero(~occupied)
    return (
        ref_positions[vacancy_indices],
        ref_fractional[vacancy_indices],
        matched_distance[vacancy_indices],
    )


def gaussian_density(fractional_positions, cell, spacing, sigma):
    """Build periodic Gaussian density using CIC deposition and FFT convolution."""
    lengths = np.linalg.norm(cell, axis=1)
    shape = np.maximum(np.ceil(lengths / spacing).astype(int), 1)
    occupancy = np.zeros(shape, dtype=float)

    # Cloud-in-cell deposition places each atom on its eight surrounding grid
    # points. It is vectorized and avoids the old atom-by-atom 3-D stencil loop.
    scaled = (fractional_positions % 1.0) * shape
    lower = np.floor(scaled).astype(int)
    remainder = scaled - lower
    for offset in np.ndindex(2, 2, 2):
        offset = np.asarray(offset)
        weights = np.prod(np.where(offset, remainder, 1.0 - remainder), axis=1)
        indices = (lower + offset) % shape
        np.add.at(occupancy, tuple(indices.T), weights)

    # In reciprocal space a Gaussian convolution is multiplication by
    # exp(-sigma^2 |k|^2 / 2). This remains valid for triclinic cells because
    # reciprocal vectors are built from the full cell matrix.
    modes = np.meshgrid(
        np.fft.fftfreq(shape[0]) * shape[0],
        np.fft.fftfreq(shape[1]) * shape[1],
        np.fft.rfftfreq(shape[2]) * shape[2],
        indexing="ij",
    )
    reciprocal_modes = np.stack(modes, axis=-1) @ np.linalg.inv(cell)
    wavevector_squared = (2 * np.pi) ** 2 * np.sum(reciprocal_modes**2, axis=-1)
    gaussian_kernel = np.exp(-0.5 * sigma**2 * wavevector_squared)
    return np.fft.irfftn(
        np.fft.rfftn(occupancy) * gaussian_kernel, s=shape
    ).real


def strongest_separated_peaks(deficit, cell, pbc, number, minimum_distance):
    """Select separated positive deficits without a costly 3-D maximum filter."""
    flat = deficit.ravel()
    candidate_count = min(flat.size, max(4096, number * 256))

    while True:
        candidates = np.argpartition(flat, -candidate_count)[-candidate_count:]
        candidates = candidates[np.argsort(flat[candidates])[::-1]]
        positions = []
        fractions = []
        for candidate in candidates:
            if flat[candidate] <= 0:
                break
            index = np.asarray(np.unravel_index(candidate, deficit.shape))
            fractional = index / np.asarray(deficit.shape)
            position = fractional @ cell
            if positions:
                distance = mic_distances(
                    np.asarray(positions), np.asarray([position]), cell, pbc
                ).min()
                if distance < minimum_distance:
                    continue
            positions.append(position)
            fractions.append(fractional)
            if len(positions) == number:
                return np.asarray(positions), np.asarray(fractions)
        if candidate_count == flat.size:
            return np.asarray(positions), np.asarray(fractions)
        candidate_count = min(flat.size, candidate_count * 2)


def density_vacancies(reference, structure, element, number, spacing, sigma, minimum_distance):
    """Locate density deficits directly in the current structure's cell."""
    _, reference_fractional = element_positions(reference, element)
    _, actual_fractional = element_positions(structure, element)
    if len(reference_fractional) == 0:
        raise ValueError(f"Reference structure contains no {element!r} atoms")

    actual_density = gaussian_density(
        actual_fractional, structure.cell.array, spacing, sigma
    )
    reference_density = gaussian_density(
        reference_fractional, structure.cell.array, spacing, sigma
    )
    deficit = reference_density - actual_density
    positions, fractions = strongest_separated_peaks(
        deficit, structure.cell, structure.pbc, number, minimum_distance
    )
    return positions, fractions, np.full(len(positions), np.nan)


def add_markers(atoms, positions, marker):
    """Return a copy of ``atoms`` with vacancy positions added as dummy atoms."""
    marked = atoms.copy()
    if len(positions) and marker.lower() != "none":
        marked += Atoms(symbols=[marker] * len(positions), positions=positions)
        marked.set_cell(atoms.cell)
        marked.pbc = atoms.pbc
    return marked


def analyse_frame(frame, atoms, reference, args, reference_element_count):
    """Analyse one frame; kept top-level so it can run in worker processes."""
    _, actual_element = element_positions(atoms, args.element)
    if args.method == "ws":
        positions, fractions, distances = wigner_seitz_vacancies(
            reference, atoms, args.element, args.tolerance
        )
    else:
        number = args.number
        if number is None:
            number = max(reference_element_count - len(actual_element), 1)
        positions, fractions, distances = density_vacancies(
            reference, atoms, args.element, number, args.spacing, args.sigma,
            args.minimum_distance,
        )
    return frame, atoms, positions, fractions, distances


def initialise_worker(reference, args, reference_element_count):
    """Store shared analysis inputs once per process, avoiding per-frame copies."""
    global _WORKER_REFERENCE, _WORKER_ARGUMENTS, _WORKER_REFERENCE_COUNT
    _WORKER_REFERENCE = reference
    _WORKER_ARGUMENTS = args
    _WORKER_REFERENCE_COUNT = reference_element_count


def analyse_frame_worker(task):
    frame, atoms = task
    return analyse_frame(
        frame, atoms, _WORKER_REFERENCE, _WORKER_ARGUMENTS, _WORKER_REFERENCE_COUNT
    )


def main():
    parser = argparse.ArgumentParser(
        description="Locate oxygen-vacancy coordinates in a structure/trajectory."
    )
    parser.add_argument("reference", help="Defect-free reference structure")
    parser.add_argument("input", help="Defective structure or ASE-readable trajectory")
    parser.add_argument("--element", default="O", help="Element vacancy to locate (default: O)")
    parser.add_argument(
        "--method", choices=("density", "ws"), default="density",
        help="density: current-cell Gaussian density deficit (default); ws: reference-site matching",
    )
    parser.add_argument(
        "--tolerance", type=float, default=1.2,
        help="Maximum reference-site assignment distance in Angstrom for ws (default: 1.2)",
    )
    parser.add_argument(
        "--number", type=int,
        help="Number of density-deficit peaks to retain (default: O count difference)",
    )
    parser.add_argument("--spacing", type=float, default=0.2, help="Density-grid spacing in Angstrom")
    parser.add_argument("--sigma", type=float, default=0.5, help="Gaussian width in Angstrom")
    parser.add_argument("--minimum-distance", type=float, default=2.0,help="Minimum separation of density peaks in Angstrom")
    parser.add_argument("--cores", type=int, default=1,help="Worker processes for independent trajectory frames (default: 1)")
    parser.add_argument("--marker", default="X", help="Dummy element marking vacancies; use 'none' to omit")
    parser.add_argument("-o", "--output", default="oxygen_vacancies.extxyz", help="Marked trajectory output")
    parser.add_argument("--report", default="oxygen_vacancies.csv", help="Vacancy coordinate report")
    args = parser.parse_args()

    reference = read(args.reference, index=0)
    trajectory = read(args.input, index=":")
    if not trajectory:
        raise ValueError("No structures were read from the input file")
    if args.cores < 1:
        raise ValueError("--cores must be at least 1")

    _, reference_oxygen = element_positions(reference, args.element)
    marked_frames = []
    report_rows = []

    tasks = list(enumerate(trajectory))
    if args.cores > 1 and len(tasks) > 1:
        with ProcessPoolExecutor(
            max_workers=args.cores,
            initializer=initialise_worker,
            initargs=(reference, args, len(reference_oxygen)),
        ) as executor:
            analyses = list(executor.map(analyse_frame_worker, tasks))
    else:
        analyses = [
            analyse_frame(frame, atoms, reference, args, len(reference_oxygen))
            for frame, atoms in tasks
        ]

    for frame, atoms, positions, fractions, distances in analyses:
        if args.method == "density":
            # Density positions are already in the current structure's cell.
            current_positions = positions
        else:
            # Wigner-Seitz positions are reference sites, so map them to the
            # current cell only for direct visualisation.
            current_positions = fractions @ atoms.cell.array
        marked_frames.append(add_markers(atoms, current_positions, args.marker))
        print(f"Frame {frame}: {len(positions)} {args.element} vacancy candidate(s)")
        for site, (position, fractional, distance) in enumerate(
            zip(current_positions, fractions, distances), start=1
        ):
            report_rows.append(
                [frame, site, args.element, *fractional, *position, distance, args.method]
            )

    write(args.output, marked_frames, format="extxyz")
    with open(args.report, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "frame", "site", "element", "fx", "fy", "fz", "x_A", "y_A", "z_A",
            "assignment_distance_A", "method",
        ])
        writer.writerows(report_rows)
    print(f"Saved marked structures: {args.output}")
    print(f"Saved vacancy coordinates: {args.report}")


if __name__ == "__main__":
    main()
