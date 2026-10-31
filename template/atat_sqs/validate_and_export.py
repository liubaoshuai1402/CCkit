#!/usr/bin/env python3
# CCkit 功能说明：检查固定胞 SQS 的组成、晶胞及位点，将占位导出为 POSCAR_sqs。
"""Validate a CCkit ATAT design and transfer SQS occupations to reference sites.

This helper is copied into each job directory and needs NumPy and pymatgen.
VASP and ATAT structure contents are parsed with pymatgen, not custom parsers.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import numpy as np
from pymatgen.core import Structure
from pymatgen.io.atat import Mcsqs
from pymatgen.io.vasp import Poscar


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def resolve_path(base: Path, requested: str) -> Path:
    """Resolve a bare filename beside its input; honor explicit directories."""
    path = Path(requested).expanduser()
    if not path.is_absolute() and not any(separator in requested for separator in ("/", "\\")):
        return base / path
    return path.resolve()


def read_atat(path: Path) -> Structure:
    """Use pymatgen's reader for rndstr.in and bestsqs.out headers and sites."""
    try:
        structure = Mcsqs.structure_from_str(path.read_text(encoding="utf-8-sig"))
    except (ValueError, IndexError, KeyError) as error:
        raise ValueError(f"Cannot parse ATAT structure {path}: {error}") from error
    require(np.isfinite(structure.lattice.matrix).all()
            and np.isfinite(structure.frac_coords).all(), f"Non-finite ATAT geometry: {path}")
    return structure


def check_inputs(directory: Path) -> tuple[Poscar, dict]:
    """Check reference geometry, random occupations and the fixed-cell design."""
    config = json.loads((directory / "design.json").read_text(encoding="utf-8"))
    require(config["schema_version"] == 1, "Unsupported design.json version")
    reference = Poscar.from_file(directory / "POSCAR.reference", check_for_potcar=False,
                                 read_velocities=False)
    structure = reference.structure
    require(structure.is_ordered, "Reference POSCAR must have ordered sites")
    require(len(structure) == config["atom_count"], "Reference atom count differs from design")
    require(math.isfinite(config["site_tolerance_A"]) and config["site_tolerance_A"] > 0,
            "Invalid site mapping tolerance")
    require(np.isfinite(structure.lattice.matrix).all()
            and np.isfinite(structure.frac_coords).all()
            and np.linalg.det(structure.lattice.matrix) > 1e-10,
            "Reference must have finite geometry and a non-singular right-handed cell")
    host_count = sum(site.specie.symbol == config["host"] for site in structure)
    require(host_count == config["host_site_count"] > 0, "Host site count differs from design")
    require(sum(config["mixed_counts"].values()) == host_count, "Invalid mixed-site counts")
    distances = structure.lattice.get_all_distances(structure.frac_coords, structure.frac_coords)
    np.fill_diagonal(distances, np.inf)
    require(np.min(distances) > 2 * config["site_tolerance_A"],
            "Reference sites are too close for unambiguous mapping")
    random = read_atat(directory / "rndstr.in")
    require(len(random) == len(structure), "rndstr.in site count differs from reference")
    require(np.allclose(random.lattice.matrix, structure.lattice.matrix, rtol=0, atol=1e-10),
            "rndstr.in changed the reference cell")
    require(np.allclose(random.frac_coords, structure.frac_coords, rtol=0, atol=1e-12),
            "rndstr.in changed reference coordinates or site order")
    for index, (original, site) in enumerate(zip(structure, random), 1):
        expected = ({symbol: count / host_count for symbol, count in config["mixed_counts"].items()}
                    if original.specie.symbol == config["host"] else {original.specie.symbol: 1.0})
        actual = {species.symbol: value for species, value in site.species.items()}
        require(actual.keys() == expected.keys()
                and all(abs(actual[key] - value) < 1e-12 for key, value in expected.items()),
                f"Incorrect random occupations at reference site {index}")
    tokens = (directory / "sqscell.out").read_text(encoding="ascii").split()
    require(len(tokens) == 10 and tokens[0] == "1", "sqscell.out must specify exactly one cell")
    require(np.array_equal(np.array([float(value) for value in tokens[1:]]).reshape(3, 3), np.eye(3)),
            "sqscell.out must use identity (ATAT >= 3.07 convention)")
    params = [float(value) for value in (directory / "sqsparam.in").read_text().split()]
    require(params == [1.0, 1.0, 0.0, 1.0], "Unexpected sqsparam.in; expected wr wn wd T = 1 1 0 1")
    print(f"INPUT CHECK PASSED: {config['formula']}; {len(structure)} fixed reference sites.")
    return reference, config


def check_groups(path: Path, config: dict) -> None:
    """Check integer occupations in each ATAT symmetry group.

    pymatgen reads structures but does not retain the blank-line grouping of
    rndstrgrp.out. Parse only these separators and the occupation labels here.
    """
    lines = path.read_text(encoding="utf-8-sig").strip().splitlines()
    require(bool(lines), f"Empty symmetry group file: {path}")
    axes_lines = 3 if len(lines[0].split()) == 3 else 1
    groups = []
    current = []
    for line in [*lines[axes_lines + 3:], ""]:
        if not line.strip():
            if current:
                groups.append(current)
                current = []
        else:
            fields = line.split()
            require(len(fields) >= 4, f"Invalid symmetry group site: {line}")
            current.append("".join(fields[3:]))
    require(sum(map(len, groups)) == config["atom_count"], "Symmetry group site count differs from design")
    mixed_total = 0
    for group in groups:
        require(len(set(group)) == 1, "Symmetry group has inconsistent occupation labels")
        if "=" not in group[0]:
            continue
        mixed_total += len(group)
        for symbol, count in config["mixed_counts"].items():
            require((count * len(group)) % config["host_site_count"] == 0,
                    f"Symmetry group of {len(group)} sites cannot realize integer {symbol} counts. "
                    "Check lattice symmetry and composition; the cell has not been expanded.")
    require(mixed_total == config["host_site_count"], "Incorrect number of mixed sites in symmetry groups")
    print(f"SYMMETRY CHECK PASSED: group sizes {[len(group) for group in groups]}.")


def export(sqs_path: Path, output: Path, report: Path, reference: Poscar, config: dict) -> None:
    """Map occupations with periodic distances and preserve reference geometry.

    Minimum-image distances are computed by pymatgen, including skewed cells.
    Only species labels are transferred; reference selective dynamics is kept.
    """
    original = reference.structure
    sqs = read_atat(sqs_path)
    require(sqs.is_ordered, "bestsqs.out must contain fully occupied chemical sites")
    require(len(sqs) == len(original), "SQS atom count differs from reference")
    require(np.allclose(sqs.lattice.matrix, original.lattice.matrix, rtol=0, atol=1e-8),
            "SQS changed reference cell vectors, orientation or vector order")
    counts = Counter(site.specie.symbol for site in sqs)
    require(dict(counts) == config["expected_counts"], f"Incorrect SQS composition: {dict(counts)}")
    distances = original.lattice.get_all_distances(sqs.frac_coords, original.frac_coords)
    mapping = np.argmin(distances, axis=1)
    residuals = distances[np.arange(len(sqs)), mapping]
    require(np.all(residuals <= config["site_tolerance_A"]),
            f"SQS site cannot map to reference: maximum residual {np.max(residuals):.6g} A")
    require(len(set(mapping.tolist())) == len(original), "Duplicate assignment to a reference site")
    occupations = [""] * len(original)
    for site, index in zip(sqs, mapping):
        label = site.specie.symbol
        original_label = original[int(index)].specie.symbol
        allowed = config["mixed_counts"] if original_label == config["host"] else {original_label: 1}
        require(label in allowed, f"SQS changed a fixed occupation at reference site {index + 1}")
        occupations[int(index)] = label
    order = [index for symbol in config["species_order"]
             for index, label in enumerate(occupations) if label == symbol]
    result = original.copy()
    for index, label in enumerate(occupations):
        result.replace(index, label)
    result = Structure.from_sites([result[index] for index in order])
    selective = reference.selective_dynamics
    poscar = Poscar(result, comment=f"{config['formula']} | fixed reference geometry | ATAT SQS",
                    selective_dynamics=None if selective is None else np.asarray(selective)[order],
                    sort_structure=False)
    by_species = {symbol: [index + 1 for index, label in enumerate(occupations) if label == symbol]
                  for symbol in config["species_order"]}
    solute_indices = [index for index, label in enumerate(occupations)
                      if label in config["mixed_counts"] and label != config["host"]
                      and original[index].specie.symbol == config["host"]]
    pairs = []
    if len(solute_indices) > 1:
        pair_distances = original.lattice.get_all_distances(
            original.frac_coords[solute_indices], original.frac_coords[solute_indices])
        for row, left in enumerate(solute_indices):
            for column in range(row + 1, len(solute_indices)):
                right = solute_indices[column]
                pairs.append({"elements": [occupations[left], occupations[right]],
                              "original_sites_1based": [left + 1, right + 1],
                              "distance_A": float(pair_distances[row, column])})
    data = {
        "source_sqs": str(sqs_path.resolve()),
        "counts": dict(counts),
        "cell_vectors_A": original.lattice.matrix.tolist(),
        "cell_volume_A3": original.volume,
        "maximum_mapping_residual_A": float(np.max(residuals)),
        "mapping_tolerance_A": config["site_tolerance_A"],
        "original_sites_1based_by_species": by_species,
        "solute_pairs": pairs,
        "POSCAR_species_order": config["species_order"],
        "POSCAR_to_original_site_1based": [index + 1 for index in order],
        "geometry_policy": "Transfer chemical occupations to reference cell/sites; preserve selective dynamics",
        "sqs_quality": "Not assessed by converter; inspect bestcorr.out and mcsqs.log",
    }
    require(output != report, "Structure and report paths must differ")
    require(not output.exists(), f"Output exists; choose another --output: {output}")
    require(not report.exists(), f"Report exists; choose another --report: {report}")
    for path in (output, report):
        path.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(poscar.get_str(direct=True, significant_figures=16))
    with report.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")
    print(f"EXPORT PASSED: {output}; maximum mapping residual {np.max(residuals):.6g} A")
    print(f"Species order: {' '.join(config['species_order'])}; counts: {dict(counts)}")
    print(f"Report: {report}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent,
                        help="Design/run directory (default: directory containing this helper)")
    parser.add_argument("--check-inputs", action="store_true", help="Check inputs without exporting")
    parser.add_argument("--groups", help="Check ATAT rndstrgrp.out symmetry group integrality")
    parser.add_argument("--sqs", default="bestsqs.out", help="ATAT best structure")
    parser.add_argument("-o", "--output", default="POSCAR_sqs",
                        help="VASP output; default/bare name is beside the SQS input")
    parser.add_argument("--report", default="validation_report.json",
                        help="JSON report; default/bare name is beside the SQS input")
    args = parser.parse_args()
    directory = args.directory.expanduser().resolve()
    try:
        reference, config = check_inputs(directory)
        if args.groups:
            check_groups(resolve_path(directory, args.groups), config)
        if not args.check_inputs:
            sqs = resolve_path(directory, args.sqs)
            export(sqs, resolve_path(sqs.parent, args.output), resolve_path(sqs.parent, args.report),
                   reference, config)
    except (ValueError, OSError, KeyError, IndexError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
