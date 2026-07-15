import numpy as np
import argparse
from ase.io import read, write
from scipy.ndimage import maximum_filter
from multiprocessing import Pool, cpu_count


def load_structure(filename):
    return read(filename, index=0)


def gaussian_density(atoms, element, spacing, sigma, ref_cell):

    cell = ref_cell

    length = np.linalg.norm(cell, axis=1)

    ngrid = np.ceil(length / spacing).astype(int)

    rho = np.zeros(ngrid)

    inv_ref = np.linalg.inv(cell)
    inv_atom = np.linalg.inv(atoms.cell.array)

    symbols = np.array(atoms.get_chemical_symbols())

    positions = atoms.positions[symbols == element]

    cutoff = 3 * sigma

    # 每个方向不同网格尺寸
    grid_spacing = length / ngrid

    radius = np.ceil(cutoff / grid_spacing).astype(int)

    for pos in positions:
        # 当前结构 -> 分数坐标
        frac = pos @ inv_atom

        frac %= 1.0

        # 映射到reference晶胞
        pos = frac @ cell

        center = np.floor(frac * ngrid).astype(int)

        for i in range(-radius[0], radius[0] + 1):
            for j in range(-radius[1], radius[1] + 1):
                for k in range(-radius[2], radius[2] + 1):
                    idx = center + np.array([i, j, k])

                    idx %= ngrid

                    frac_grid = idx / ngrid

                    grid_pos = frac_grid @ cell

                    d = grid_pos - pos

                    # minimum image
                    d = (d - np.round(d @ inv_ref)) @ cell

                    r2 = np.dot(d, d)

                    if r2 < cutoff**2:
                        rho[tuple(idx)] += np.exp(-r2 / (2 * sigma * sigma))

    return rho


def find_vacancies(rho_ref, rho_def, ref_cell, nvac, min_dist):

    deficit = rho_ref - rho_def

    peaks = deficit == maximum_filter(deficit, size=5)

    ids = np.argwhere(peaks)

    values = deficit[peaks]

    order = np.argsort(values)[::-1]

    cell = ref_cell

    inv = np.linalg.inv(cell)

    ngrid = np.array(deficit.shape)

    vacancies = []

    for idx in ids[order]:
        frac = idx / ngrid

        pos = frac @ cell

        keep = True

        for v in vacancies:
            d = pos - v

            d = (d - np.round(d @ inv)) @ cell

            if np.linalg.norm(d) < min_dist:
                keep = False

                break

        if keep:
            vacancies.append(pos)

        if len(vacancies) >= nvac:
            break

    return np.array(vacancies)


def insert_atoms(atoms, positions, symbol):

    atoms = atoms.copy()

    for p in positions:
        atoms.append(symbol)

        atoms.positions[-1] = p

    return atoms


def process_frame(data):

    index, atoms, rho_ref, ref_cell, args = data

    rho_def = gaussian_density(atoms, args.element, args.spacing, args.sigma, ref_cell)

    vac = find_vacancies(rho_ref, rho_def, ref_cell, args.nvac, args.min_dist)

    print("Frame", index, "vacancy:", vac)

    return insert_atoms(atoms, vac, args.symbol)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("reference")

    parser.add_argument("input")

    parser.add_argument("--output", default="vacancy.xyz")

    parser.add_argument("--element", default="O")

    parser.add_argument("--symbol", default="X")

    parser.add_argument("--nvac", type=int, default=1)

    parser.add_argument("--spacing", type=float, default=0.2)

    parser.add_argument("--sigma", type=float, default=0.5)

    parser.add_argument("--min_dist", type=float, default=2.0)

    parser.add_argument("--cores", type=int, default=cpu_count())

    args = parser.parse_args()

    ref = load_structure(args.reference)

    ref_cell = ref.cell.array

    traj = read(args.input, index=":")

    print("Frames:", len(traj))

    rho_ref = gaussian_density(ref, args.element, args.spacing, args.sigma, ref_cell)

    tasks = []

    for i, atoms in enumerate(traj):
        tasks.append((i, atoms, rho_ref, ref_cell, args))

    with Pool(args.cores) as pool:
        results = pool.map(process_frame, tasks)

    write(args.output, results, format="extxyz")


if __name__ == "__main__":
    main()
