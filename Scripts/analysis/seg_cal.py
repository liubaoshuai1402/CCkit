"""Calculate the average grain-boundary segregation concentration.

The input is a two-column text file containing paired segregation enthalpy
and entropy values.  The implementation follows the distribution model used
in the supplied literature: skew-normal maximum-likelihood fitting for
enthalpy, linear regression for entropy statistics, a Gaussian copula for
the dependence structure, and McLean isotherm averaging.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.special import expit
from scipy.stats import norm, pearsonr, rankdata, skewnorm


ENERGY_CONSTANTS = {
    "eV": 8.617333262145e-5,
    "kJ/mol": 8.31446261815324e-3,
}


def read_enthalpy_entropy(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read paired enthalpy and entropy columns from a text or CSV file."""
    enthalpy: list[float] = []
    entropy: list[float] = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            fields = next(csv.reader([stripped]))
            if len(fields) == 1:
                fields = stripped.split()
            if len(fields) < 2:
                raise ValueError(
                    f"{path}:{line_number} must contain enthalpy and entropy columns"
                )

            try:
                enthalpy.append(float(fields[0]))
                entropy.append(float(fields[1]))
            except ValueError:
                if not enthalpy:
                    # Allow one non-numeric header row.
                    continue
                raise ValueError(
                    f"{path}:{line_number} contains non-numeric enthalpy/entropy data"
                ) from None

    if len(enthalpy) < 3:
        raise ValueError("At least three paired enthalpy/entropy rows are required")

    enthalpy_array = np.asarray(enthalpy, dtype=float)
    entropy_array = np.asarray(entropy, dtype=float)
    if not np.all(np.isfinite(enthalpy_array)) or not np.all(np.isfinite(entropy_array)):
        raise ValueError("Enthalpy and entropy values must all be finite")
    return enthalpy_array, entropy_array


def fit_enthalpy_distribution(enthalpy: np.ndarray) -> dict[str, float]:
    """Fit a skew-normal distribution by maximum likelihood."""
    if np.ptp(enthalpy) == 0:
        raise ValueError("Enthalpy values must not all be identical")
    shape, location, scale = skewnorm.fit(enthalpy)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("The fitted enthalpy scale must be positive")

    mean, variance = skewnorm.stats(shape, loc=location, scale=scale, moments="mv")
    return {
        "shape": float(shape),
        "shape_scipy": float(shape),
        "alpha_paper": float(-shape),
        "location": float(location),
        "scale": float(scale),
        "mean": float(mean),
        "variance": float(variance),
    }


def fit_entropy_distribution(
    enthalpy: np.ndarray, entropy: np.ndarray, enthalpy_stats: dict[str, float]
) -> dict[str, float]:
    """Fit ``S = S0 + chi * H`` and derive the Gaussian entropy marginal."""
    chi, intercept = np.polyfit(enthalpy, entropy, deg=1)
    entropy_mean = intercept + chi * enthalpy_stats["mean"]
    entropy_variance = chi**2 * enthalpy_stats["variance"]
    return {
        "intercept_S0": float(intercept),
        "slope_chi": float(chi),
        "mean": float(entropy_mean),
        "variance": float(entropy_variance),
        "standard_deviation": float(np.sqrt(max(entropy_variance, 0.0))),
    }


def gaussian_copula_correlation(
    enthalpy: np.ndarray, entropy: np.ndarray
) -> tuple[float, np.ndarray, np.ndarray]:
    """Estimate Gaussian-copula rho from rank-normalized paired samples."""
    if np.ptp(enthalpy) == 0 or np.ptp(entropy) == 0:
        raise ValueError(
            "Both enthalpy and entropy need nonzero variation to estimate copula rho"
        )
    n = len(enthalpy)
    uniform_enthalpy = rankdata(enthalpy, method="average") / (n + 1.0)
    uniform_entropy = rankdata(entropy, method="average") / (n + 1.0)
    z_enthalpy = norm.ppf(uniform_enthalpy)
    z_entropy = norm.ppf(uniform_entropy)
    rho = float(pearsonr(z_enthalpy, z_entropy).statistic)
    return float(np.clip(rho, -1.0, 1.0)), z_enthalpy, z_entropy


def _skew_normal_from_latent(
    latent: np.ndarray, enthalpy_stats: dict[str, float]
) -> np.ndarray:
    """Map a standard normal latent variable through the fitted H marginal."""
    probabilities = np.clip(norm.cdf(latent), np.finfo(float).eps, 1.0 - np.finfo(float).eps)
    return skewnorm.ppf(
        probabilities,
        enthalpy_stats["shape"],
        loc=enthalpy_stats["location"],
        scale=enthalpy_stats["scale"],
    )


def average_mclean_concentration(
    enthalpy_stats: dict[str, float],
    entropy_stats: dict[str, float],
    rho: float,
    bulk_concentration: float,
    temperature: float,
    energy_unit: str,
    quadrature_order: int = 60,
) -> float:
    """Integrate the McLean concentration over the fitted joint distribution."""
    if not 0.0 < bulk_concentration < 1.0:
        raise ValueError("bulk concentration must be strictly between 0 and 1")
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if quadrature_order < 8:
        raise ValueError("quadrature order must be at least 8")

    nodes, weights = np.polynomial.hermite.hermgauss(quadrature_order)
    latent = np.sqrt(2.0) * nodes
    weight_grid = np.outer(weights, weights) / np.pi
    h_grid = _skew_normal_from_latent(latent[:, None], enthalpy_stats)

    independent = latent[None, :]
    correlated = rho * latent[:, None] + np.sqrt(max(0.0, 1.0 - rho**2)) * independent
    entropy_grid = (
        entropy_stats["mean"]
        + entropy_stats["standard_deviation"] * correlated
    )
    free_energy = h_grid - temperature * entropy_grid
    exponent = free_energy / (ENERGY_CONSTANTS[energy_unit] * temperature)
    bulk_ratio = (1.0 - bulk_concentration) / bulk_concentration
    # 1 / (1 + bulk_ratio * exp(exponent)), evaluated stably for large exponents.
    local_concentration = expit(-np.log(bulk_ratio) - exponent)
    return float(np.sum(weight_grid * local_concentration))


def calculate_segregation(
    enthalpy: np.ndarray,
    entropy: np.ndarray,
    bulk_concentration: float,
    temperature: float,
    energy_unit: str,
    quadrature_order: int,
) -> dict[str, object]:
    """Run the complete segregation model and return JSON-serializable results."""
    if energy_unit not in ENERGY_CONSTANTS:
        raise ValueError(f"Unsupported energy unit: {energy_unit}")
    enthalpy_stats = fit_enthalpy_distribution(enthalpy)
    entropy_stats = fit_entropy_distribution(enthalpy, entropy, enthalpy_stats)
    rho, _, _ = gaussian_copula_correlation(enthalpy, entropy)
    average = average_mclean_concentration(
        enthalpy_stats,
        entropy_stats,
        rho,
        bulk_concentration,
        temperature,
        energy_unit,
        quadrature_order,
    )
    return {
        "sample_count": int(len(enthalpy)),
        "bulk_concentration": float(bulk_concentration),
        "temperature_K": float(temperature),
        "energy_unit": energy_unit,
        "enthalpy_distribution": enthalpy_stats,
        "entropy_distribution": entropy_stats,
        "gaussian_copula_pearson_rho": rho,
        "average_grain_boundary_concentration": average,
        "quadrature_order": int(quadrature_order),
    }


def output_path(input_path: Path, requested: str | None) -> Path:
    """Resolve a default or bare output name next to the input data file."""
    if requested is None:
        return input_path.with_name(f"{input_path.stem}_segregation.json")
    candidate = Path(requested)
    if not candidate.parent or str(candidate.parent) == ".":
        return input_path.parent / candidate.name
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate average grain-boundary segregation from paired "
            "enthalpy/entropy data using the Cho distribution model."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Two-column text/CSV file: segregation enthalpy first, entropy second",
    )
    parser.add_argument(
        "bulk_concentration",
        type=float,
        help="Bulk solute concentration X^C, strictly between 0 and 1",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        required=True,
        metavar="K",
        help="Temperature in K",
    )
    parser.add_argument(
        "--energy-unit",
        choices=tuple(ENERGY_CONSTANTS),
        default="eV",
        help="Energy unit for enthalpy and T*entropy (default: eV)",
    )
    parser.add_argument(
        "--quadrature-order",
        type=int,
        default=60,
        help="Gauss-Hermite order per latent dimension (default: 60)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="JSON output path; a bare name is written next to the input file",
    )
    args = parser.parse_args()

    input_path = args.input.expanduser()
    if not input_path.is_file():
        parser.error(f"input file does not exist: {input_path}")
    if not 0.0 < args.bulk_concentration < 1.0:
        parser.error("bulk_concentration must be strictly between 0 and 1")
    if args.temperature <= 0:
        parser.error("--temperature must be positive")

    enthalpy, entropy = read_enthalpy_entropy(input_path)
    result = calculate_segregation(
        enthalpy,
        entropy,
        args.bulk_concentration,
        args.temperature,
        args.energy_unit,
        args.quadrature_order,
    )
    destination = output_path(input_path, args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "Average grain-boundary concentration: "
        f"{result['average_grain_boundary_concentration']:.8g}"
    )
    print(f"Saved result: {destination.resolve()}")


if __name__ == "__main__":
    main()
