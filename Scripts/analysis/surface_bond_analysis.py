# CCkit 功能说明：按金属原子的 z 高度分层，统计金属–氧键长并绘制窄峰分布。
"""Analyze POSCAR M-O neighbors by Cartesian-z layer using pymatgen.

Layers have a bounded z span. Gaussian KDE uses an absolute smoothing width
so single-bond and identical-length samples also have a defined curve.
"""

import argparse
import math
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from pymatgen.core import Element, Lattice, Structure
from pymatgen.io.vasp import Poscar


@dataclass(frozen=True)
class Bond:
    """One M-O neighbor, including the oxygen's lattice image and distance in Angstrom."""

    metal: int
    oxygen: int
    image: tuple[int, int, int]
    length: float


@dataclass
class Layer:
    """Metal sites in one height interval and the bonds assigned to those sites."""

    indices: list[int]
    bonds: list[Bond] = field(default_factory=list)


@dataclass(frozen=True)
class LengthHistogram:
    """Grouped length centers in Angstrom, integer frequencies and display widths."""

    centers: np.ndarray
    counts: np.ndarray
    widths: np.ndarray


def group_layers(structure: Structure, metals: set[str], tolerance: float) -> list[Layer]:
    """Group metals by bounded z span in Angstrom and return layers top to bottom."""
    indices = sorted(
        (i for i, site in enumerate(structure) if site.specie.symbol in metals),
        key=lambda i: (structure[i].z, i),
    )
    layers: list[Layer] = []
    for index in indices:
        if (
            not layers
            or structure[index].z - structure[layers[-1].indices[0]].z > tolerance + 1e-8
        ):
            layers.append(Layer([index]))
        else:
            layers[-1].indices.append(index)
    layers.reverse()
    return layers


def collect_bonds(structure: Structure, layers: list[Layer], cutoff: float) -> None:
    """Assign each M-to-O image neighbor to its metal's layer, counting each once."""
    metal_layers = {index: layer for layer in layers for index in layer.indices}
    centers, neighbors, images, distances = structure.get_neighbor_list(cutoff)
    for metal, oxygen, image, distance in zip(centers, neighbors, images, distances):
        if metal not in metal_layers or structure[oxygen].specie.symbol != "O":
            continue
        if not np.isfinite(distance) or distance <= 1e-8:
            raise ValueError(f"Invalid M-O distance between sites {metal} and {oxygen}")
        if distance <= cutoff + 1e-8:
            shift = tuple(int(value) for value in np.rint(image))
            metal_layers[metal].bonds.append(Bond(int(metal), int(oxygen), shift, float(distance)))
    for layer in layers:
        layer.bonds.sort(key=lambda bond: (bond.metal, bond.oxygen, bond.image))


def gaussian_density(values: np.ndarray, grid: np.ndarray, bandwidth: float) -> np.ndarray:
    """Evaluate a normalized Gaussian KDE with an absolute sigma in Angstrom.

    Repeated lengths retain their multiplicities. Small blocks limit working
    memory, and the formula needs no sample covariance or artificial jitter.
    """
    density = np.zeros_like(grid)
    if values.size:
        unique, counts = np.unique(values, return_counts=True)
        for start in range(0, len(unique), 64):
            scaled = (grid[:, None] - unique[None, start:start + 64]) / bandwidth
            density += np.exp(-0.5 * scaled**2) @ counts[start:start + 64]
        density /= values.size * bandwidth * math.sqrt(2 * math.pi)
    return density


def length_histogram(values: np.ndarray, tolerance: float, bar_width: float) -> LengthHistogram:
    """Group near-equal lengths by bounded total span and count every sample once.

    Group centers are sample means. The grouping tolerance and maximum bar
    width are in Angstrom. Display widths leave gaps between adjacent groups.
    """
    ordered = np.sort(values)
    if not ordered.size:
        return LengthHistogram(np.array([]), np.array([], dtype=int), np.array([]))
    starts = [0]
    for index in range(1, len(ordered)):
        if ordered[index] - ordered[starts[-1]] > tolerance:
            starts.append(index)
    boundaries = np.array(starts + [len(ordered)])
    counts = np.diff(boundaries)
    centers = np.array([
        ordered[start:stop].mean()
        for start, stop in zip(boundaries[:-1], boundaries[1:])
    ])
    gaps = np.diff(centers)
    nearest_gap = np.minimum(np.r_[np.inf, gaps], np.r_[gaps, np.inf])
    widths = np.minimum(bar_width, 0.8 * nearest_gap)
    return LengthHistogram(centers, counts, widths)


def distribution_grid(
    lengths: list[np.ndarray], cutoff: float, bandwidth: float, bar_width: float,
) -> np.ndarray:
    """Build a common KDE grid covering the curves and centered bars."""
    available = [values for values in lengths if values.size]
    if available:
        padding = max(4 * bandwidth, bar_width / 2)
        lower = max(0.0, min(float(values.min()) for values in available) - padding)
        upper = max(float(values.max()) for values in available) + padding
    else:
        lower, upper = 0.0, cutoff
    if not math.isfinite(upper) or upper <= lower:
        raise ValueError("Bandwidth is outside the numerical range of the bond lengths")
    grid_intervals = (upper - lower) / bandwidth * 8
    if not math.isfinite(grid_intervals) or grid_intervals > 49999:
        raise ValueError("Bandwidth is too small for the plotted bond-length range")
    grid_count = max(512, math.ceil(grid_intervals) + 1)
    return np.linspace(lower, upper, grid_count)


def write_tables(
    output: Path, structure: Structure, layers: list[Layer], lengths: list[np.ndarray],
    grid: np.ndarray, densities: list[np.ndarray], histograms: list[LengthHistogram], metadata: str,
) -> None:
    """Write raw bonds, layer statistics, histogram frequencies and KDE curves as text."""
    with (output / "bonds.txt").open("w", encoding="utf-8") as handle:
        handle.write(metadata)
        handle.write(
            "# layer metal_index metal_element metal_z_A oxygen_index "
            "image_a image_b image_c length_A\n"
        )
        for number, layer in enumerate(layers, start=1):
            for bond in layer.bonds:
                element = structure[bond.metal].specie.symbol
                image = " ".join(str(value) for value in bond.image)
                handle.write(
                    f"{number} {bond.metal} {element} {structure[bond.metal].z:.8f} "
                    f"{bond.oxygen} {image} {bond.length:.10f}\n"
                )

    with (output / "layers.txt").open("w", encoding="utf-8") as handle:
        handle.write(metadata)
        handle.write(
            "# layer z_min_A z_max_A z_mean_A n_metals n_bonded_metals n_bonds "
            "mean_A std_population_A min_A median_A max_A mean_coordination metal_indices\n"
        )
        for number, (layer, values) in enumerate(zip(layers, lengths), start=1):
            heights = np.array([structure[index].z for index in layer.indices])
            stats = (
                [values.mean(), values.std(ddof=0), values.min(), np.median(values), values.max()]
                if values.size else [float("nan")] * 5
            )
            bonded_metals = len({bond.metal for bond in layer.bonds})
            handle.write(
                f"{number} {heights.min():.8f} {heights.max():.8f} {heights.mean():.8f} "
                f"{len(layer.indices)} {bonded_metals} {len(values)} "
                + " ".join(f"{value:.10f}" for value in stats)
                + f" {len(values) / len(layer.indices):.8f} "
                + ",".join(str(index) for index in layer.indices) + "\n"
            )

    with (output / "kde.txt").open("w", encoding="utf-8") as handle:
        handle.write(metadata)
        handle.write("# layer length_A density_per_A\n")
        for number, (values, density) in enumerate(zip(lengths, densities), start=1):
            if values.size:
                for position, value in zip(grid, density):
                    handle.write(f"{number} {position:.10f} {value:.10e}\n")


    with (output / "histogram.txt").open("w", encoding="utf-8") as handle:
        handle.write(metadata)
        handle.write("# layer mean_length_A bond_count display_width_A\n")
        for number, histogram in enumerate(histograms, start=1):
            for center, count, width in zip(histogram.centers, histogram.counts, histogram.widths):
                handle.write(f"{number} {center:.10f} {count} {width:.10e}\n")


def plot_distributions(
    output: Path, structure: Structure, layers: list[Layer], lengths: list[np.ndarray],
    grid: np.ndarray, densities: list[np.ndarray], histograms: list[LengthHistogram], bandwidth: float,
) -> int:
    """Plot grouped frequency histograms, KDE curves and length marks, eight layers per page."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    plt.rcParams.update({
        "font.family": "Arial",
        "font.weight": "bold",
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
        "figure.titleweight": "bold",
        "axes.formatter.use_mathtext": False,
        "text.usetex": False,
    })
    bond_label = " / ".join(sorted({
        f"{structure[index].specie.symbol}-O" for layer in layers for index in layer.indices
    }))
    for page, start in enumerate(range(0, len(layers), 8), start=1):
        count = min(8, len(layers) - start)
        columns = min(2, count)
        rows = math.ceil(count / columns)
        figure, axes = plt.subplots(
            rows, columns, figsize=(6 * columns, 4.0 * rows), squeeze=False, sharex=True,
            constrained_layout=True,
        )
        try:
            for offset, axis in enumerate(axes.flat):
                if offset >= count:
                    axis.set_visible(False)
                    continue
                index = start + offset
                layer, values = layers[index], lengths[index]
                heights = [structure[site].z for site in layer.indices]
                layer_bond_label = " / ".join(sorted({
                    f"{structure[site].specie.symbol}-O" for site in layer.indices
                }))
                if values.size:
                    histogram = histograms[index]
                    axis.bar(
                        histogram.centers, histogram.counts, width=histogram.widths,
                        align="center", color="#8db9db", alpha=0.75, linewidth=0,
                        label="Histogram (counts)",
                    )
                    density_axis = axis.twinx()
                    density_axis.plot(
                        grid, densities[index], color="#c34930", linewidth=2.2,
                        label="Gaussian KDE",
                    )
                    density_axis.set_ylim(0, float(densities[index].max()) * 1.35)
                    density_axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
                    density_axis.set_ylabel("KDE density (Å⁻¹)", color="#c34930")
                    density_axis.tick_params(axis="y", labelcolor="#c34930")
                    # Representative marks share exactly the same centers as the bars.
                    axis.plot(
                        histogram.centers, np.full(len(histogram.centers), 0.025), "|",
                        transform=axis.get_xaxis_transform(), color="#23465e", markersize=6,
                        label="Group mean lengths",
                    )
                    handles, labels = axis.get_legend_handles_labels()
                    kde_handles, kde_labels = density_axis.get_legend_handles_labels()
                    density_axis.legend(
                        handles + kde_handles, labels + kde_labels, loc="upper right",
                        prop={"family": "Arial", "weight": "bold", "size": 8},
                        frameon=True, facecolor="white", edgecolor="#dddddd",
                        framealpha=0.95, borderpad=0.7, labelspacing=0.5,
                    )
                else:
                    axis.text(
                        0.5, 0.5, f"No {layer_bond_label} neighbors within cutoff", ha="center",
                        transform=axis.transAxes,
                    )
                axis.set_title(
                    f"Layer {index + 1} | {layer_bond_label} | "
                    f"z = {min(heights):.2f}-{max(heights):.2f} Å\n"
                    f"{len(layer.indices)} metal sites, {len(values)} bonds", fontsize=10, pad=10,
                )
                axis.set_xlim(grid[0], grid[-1])
                count_limit = float(histograms[index].counts.max()) * 1.35 if values.size else 1.0
                axis.set_ylim(0, count_limit)
                axis.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
                axis.set_xlabel(f"{layer_bond_label} distance (Å)")
                axis.tick_params(axis="x", which="both", bottom=True, labelbottom=True)
                axis.set_ylabel("Bond count")
                axis.grid(alpha=0.15)
            figure.suptitle(
                f"Layer-resolved {bond_label} lengths | Gaussian bandwidth = {bandwidth:g} Å"
            )
            figure.savefig(output / f"distributions_{page:02d}.png", dpi=300)
        finally:
            plt.close(figure)
    return math.ceil(len(layers) / 8)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Group slab metals by z height and plot their M-O length distributions."
    )
    parser.add_argument("input", type=Path, help="POSCAR or CONTCAR with element symbols")
    parser.add_argument("--metals", nargs="+", help="Metal symbols to include (default: all metals)")
    parser.add_argument("--cutoff", type=float, default=3.0, help="M-O cutoff in Angstrom (default: 3)")
    parser.add_argument(
        "--layer-tol", type=float, default=1.0,
        help="Maximum Cartesian-z span of one layer in Angstrom (default: 1)",
    )
    parser.add_argument(
        "--bandwidth", type=float, default=0.02,
        help="Gaussian KDE smoothing sigma in Angstrom (default: 0.02)",
    )
    parser.add_argument(
        "--bar-width", "--bin-width", dest="bar_width", type=float, default=0.01,
        help="Maximum centered bar width in Angstrom, narrowed to leave gaps (default: 0.01)",
    )
    parser.add_argument(
        "--length-tol", type=float, default=0.001,
        help="Maximum length span per frequency group in Angstrom (default: 0.001)",
    )
    parser.add_argument(
        "--periodic-z", action="store_true",
        help="Also include c-direction periodic neighbors (default: periodic a/b only)",
    )
    parser.add_argument(
        "-o", "--output",
        help="New output directory (default: <input-stem>_surface_bonds beside input)",
    )
    args = parser.parse_args()
    for name in ("cutoff", "bandwidth", "bar_width"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            parser.error(f"--{name.replace('_', '-')} must be finite and positive")
    if not math.isfinite(args.layer_tol) or args.layer_tol < 0:
        parser.error("--layer-tol must be finite and non-negative")
    if not math.isfinite(args.length_tol) or args.length_tol < 0:
        parser.error("--length-tol must be finite and non-negative")
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        parser.error(f"POSCAR not found: {input_path}")
    output = input_path.with_name(f"{input_path.stem}_surface_bonds")
    if args.output is not None:
        output = Path(args.output).expanduser()
        if not output.is_absolute() and not any(sep in args.output for sep in ("/", "\\")):
            output = input_path.parent / output
    output = output.absolute()

    try:
        poscar = Poscar.from_file(input_path, check_for_potcar=False, read_velocities=False)
        if not poscar.true_names:
            raise ValueError("POSCAR must identify its elements. Supply a VASP 5/6 POSCAR.")
        structure = poscar.structure
        if not len(structure) or not np.isfinite(structure.cart_coords).all():
            raise ValueError("POSCAR has no atoms or contains non-finite coordinates")
        if not np.allclose(structure.lattice.matrix[:2, 2], 0.0, atol=1e-6):
            raise ValueError("Orient the slab parallel to Cartesian xy before analyzing z layers")
        structure.lattice = Lattice(structure.lattice.matrix, pbc=(True, True, args.periodic_z))
        present = {site.specie.symbol for site in structure}
        metals = (
            set(args.metals) if args.metals
            else {symbol for symbol in present if Element(symbol).is_metal}
        )
        if not metals or any(not Element(symbol).is_metal for symbol in metals):
            raise ValueError("Select at least one metal element with --metals")
        if metals - present:
            raise ValueError(
                f"Requested metals absent from POSCAR: {', '.join(sorted(metals - present))}"
            )
        if "O" not in present:
            raise ValueError("POSCAR contains no oxygen atoms")

        layers = group_layers(structure, metals, args.layer_tol)
        collect_bonds(structure, layers, args.cutoff)
        lengths = [np.array([bond.length for bond in layer.bonds]) for layer in layers]
        grid = distribution_grid(lengths, args.cutoff, args.bandwidth, args.bar_width)
        densities = [gaussian_density(values, grid, args.bandwidth) for values in lengths]
        histograms = [length_histogram(values, args.length_tol, args.bar_width) for values in lengths]
        metadata = (
            f"# input {input_path}\n# metals {' '.join(sorted(metals))}\n"
            f"# cutoff_A {args.cutoff:g} layer_span_A {args.layer_tol:g}\n"
            f"# gaussian_bandwidth_A {args.bandwidth:g} max_bar_width_A {args.bar_width:g}\n"
            f"# histogram_length_span_A {args.length_tol:g}\n"
            f"# lattice_pbc {structure.pbc}\n"
            "# site_indices 0-based, layers 1-based from high to low stored Cartesian z\n"
            "# each oxygen lattice image is a distinct neighbor, assigned by its metal site\n"
            "# each histogram group has bounded length span and counts every bond once\n"
            "# histogram bar centers and length marks are group means, heights are counts\n"
            "# KDE is smoothing of static samples, bandwidth is not a thermal uncertainty\n"
        )
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Output already exists: {output}. Choose a new -o directory.")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Publish the complete set together so plotting errors leave no partial report.
        with tempfile.TemporaryDirectory(
            prefix=".cckit-surface-bond-", dir=output.parent,
        ) as directory:
            staging = Path(directory) / "results"
            staging.mkdir()
            write_tables(staging, structure, layers, lengths, grid, densities, histograms, metadata)
            pages = plot_distributions(
                staging, structure, layers, lengths, grid, densities, histograms, args.bandwidth,
            )
            if output.exists() or output.is_symlink():
                raise FileExistsError(f"Output appeared during analysis: {output}")
            staging.rename(output)
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        parser.error(f"Cannot analyze {input_path}: {error}")

    print(
        f"Analyzed {sum(len(layer.indices) for layer in layers)} metal sites "
        f"in {len(layers)} layers."
    )
    print(
        f"Found {sum(len(values) for values in lengths)} M-O neighbors "
        f"within {args.cutoff:g} Angstrom."
    )
    for number, values in enumerate(lengths, start=1):
        detail = f"mean {values.mean():.6f} Angstrom" if values.size else "no bonds"
        print(f"Layer {number}: {len(values)} bonds, {detail}")
    print(f"Output: {output}")
    print(f"Wrote bonds.txt, layers.txt, histogram.txt, kde.txt and {pages} distribution plot(s).")


if __name__ == "__main__":
    main()
