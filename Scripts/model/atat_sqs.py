#!/usr/bin/env python3
# CCkit 功能说明：为 POSCAR 生成固定晶胞 ATAT SQS 输入及单种子 Slurm 工作流。
"""Prepare substitutional SQS jobs without changing the input cell or sites."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import shutil

import numpy as np
from pymatgen.core import Element
from pymatgen.io.vasp import Poscar


SCRIPT_PATH = Path(__file__).resolve()
TEMPLATES = SCRIPT_PATH.parents[2] / "template" / SCRIPT_PATH.stem
IDENTITY = "1 0 0\n0 1 0\n0 0 1\n"


def parse_solutes(entries: list[str]) -> dict[str, int]:
    """Parse element=count entries; counts denote replacements of host atoms."""
    solutes = {}
    for entry in entries:
        fields = entry.split("=")
        if len(fields) != 2 or not Element.is_valid_symbol(fields[0]):
            raise ValueError(f"Invalid solute {entry!r}; use element=count, e.g. Nb=1")
        symbol, text = fields
        try:
            count = int(text)
        except ValueError as error:
            raise ValueError(f"Solute count must be an integer: {entry}") from error
        if count <= 0 or symbol in solutes:
            raise ValueError(f"Solute counts must be positive and elements unique: {entry}")
        solutes[symbol] = count
    return solutes


def output_directory(source: Path, requested: str | None, formula: str) -> Path:
    """Resolve a default or bare directory name beside the input POSCAR."""
    if requested is None:
        return source.parent / f"SQS_{formula}"
    path = Path(requested).expanduser()
    if not path.is_absolute() and not any(separator in requested for separator in ("/", "\\")):
        return source.parent / path
    return path.resolve()


def write_text(path: Path, content: str) -> None:
    """Create a UTF-8 file with Unix line endings, refusing overwrites."""
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def prepare(args: argparse.Namespace) -> Path:
    """Write a portable job directory; never run or submit ATAT here."""
    source = args.poscar.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Input POSCAR does not exist: {source}")
    for name in ("pair_cutoff", "triplet_cutoff", "corr_tol", "site_tol"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"--{name.replace('_', '-')} must be finite and positive")
    if args.triplet_cutoff > args.pair_cutoff:
        raise ValueError("--triplet-cutoff must not exceed --pair-cutoff")
    if not 0 < args.seed <= 2147483647 or not 0 < args.steps <= 2147483647:
        raise ValueError("--seed and --steps must be positive signed 32-bit integers")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", args.partition):
        raise ValueError("--partition must be one Slurm partition name (letters/digits/_.-)")

    reference = Poscar.from_file(source, check_for_potcar=False, read_velocities=False)
    structure = reference.structure
    if not structure.is_ordered or len(structure) < 2:
        raise ValueError("Input must be an ordered POSCAR with at least two sites")
    cell = structure.lattice.matrix
    if (not np.isfinite(cell).all() or abs(np.linalg.det(cell)) < 1e-10
            or not np.isfinite(structure.frac_coords).all()):
        raise ValueError("POSCAR has a singular cell or non-finite geometry")
    # pymatgen's POSCAR writer changes left-handed cells to right-handed cells.
    # Reject that case instead of silently changing the requested vectors.
    if np.linalg.det(cell) < 0:
        raise ValueError("Input must use right-handed cell vectors to preserve them on POSCAR export")
    labels = [site.specie.symbol for site in structure]
    original_counts = Counter(labels)
    host = args.host
    if host is None:
        if len(original_counts) != 1:
            raise ValueError("For a multi-element POSCAR, specify the substitutional --host")
        host = labels[0]
    if host not in original_counts:
        raise ValueError(f"Host element {host!r} is absent from POSCAR")
    solutes = parse_solutes(args.solute)
    if host in solutes:
        raise ValueError("--solute must not include the host element")
    host_count = original_counts[host]
    remaining = host_count - sum(solutes.values())
    if remaining < 0:
        raise ValueError(f"Requested solutes exceed the {host_count} available {host} sites")
    mixture = ({host: remaining} if remaining else {}) | solutes
    if len(mixture) < 2:
        raise ValueError("SQS requires at least two species on the mixed host sites")

    distances = structure.lattice.get_all_distances(structure.frac_coords, structure.frac_coords)
    np.fill_diagonal(distances, np.inf)
    if np.min(distances) <= 2 * args.site_tol:
        raise ValueError("Two periodic sites are closer than twice --site-tol; mapping is ambiguous")

    expected = original_counts.copy()
    expected[host] -= sum(solutes.values())
    expected.update(solutes)
    species_order = list(dict.fromkeys([host, *labels, *solutes]))
    species_order = [symbol for symbol in species_order if expected[symbol] > 0]
    expected = {symbol: expected[symbol] for symbol in species_order}
    formula = "".join(f"{symbol}{expected[symbol]}" for symbol in species_order)
    config = {
        "schema_version": 1,
        "formula": formula,
        "host": host,
        "host_site_count": host_count,
        "mixed_counts": mixture,
        "expected_counts": expected,
        "species_order": species_order,
        "atom_count": len(structure),
        "seed": args.seed,
        "steps": args.steps,
        "pair_cutoff_A": args.pair_cutoff,
        "triplet_cutoff_A": args.triplet_cutoff,
        "correlation_tolerance": args.corr_tol,
        "site_tolerance_A": args.site_tol,
        "partition": args.partition,
    }
    # The ATAT coordinate axes are the full input cell; all following vectors
    # and coordinates are expressed in this basis. Identity therefore fixes it.
    rows = [" ".join(f"{value:.17g}" for value in row) for row in cell]
    rows.extend(IDENTITY.rstrip().splitlines())
    occupation = ",".join(f"{symbol}={count / host_count:.17g}" for symbol, count in mixture.items())
    for site, label in zip(structure, labels):
        coordinates = " ".join(f"{value:.17g}" for value in site.frac_coords)
        rows.append(f"{coordinates} {occupation if label == host else label}")

    replacements = {
        "@@PARTITION@@": args.partition,
        "@@FORMULA@@": formula,
        "@@SEED@@": str(args.seed),
        "@@STEPS@@": str(args.steps),
        "@@ATOMS@@": str(len(structure)),
        "@@PAIR@@": f"{args.pair_cutoff:.17g}",
        "@@TRIPLET@@": f"{args.triplet_cutoff:.17g}",
        "@@TOL@@": f"{args.corr_tol:.17g}",
    }
    runner = (TEMPLATES / "run_sqs.sh.in").read_text(encoding="utf-8")
    readme = (TEMPLATES / "README.md.in").read_text(encoding="utf-8")
    helper = (TEMPLATES / "validate_and_export.py").read_text(encoding="utf-8")
    for token, value in replacements.items():
        runner = runner.replace(token, value)
        readme = readme.replace(token, value)

    destination = output_directory(source, args.output, formula)
    if destination.exists():
        raise ValueError(f"Output directory exists; choose a new -o directory: {destination}")
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source, destination / "POSCAR.reference")
    write_text(destination / "rndstr.in", "\n".join(rows) + "\n")
    write_text(destination / "sqscell.out", "1\n\n" + IDENTITY)
    write_text(destination / "sqsparam.in", "1.0 1.0 0.0 1.0\n")
    write_text(destination / "design.json", json.dumps(config, indent=2) + "\n")
    write_text(destination / "run_sqs.sh", runner)
    write_text(destination / "validate_and_export.py", helper)
    write_text(destination / "README.md", readme)
    print(f"Prepared {formula}: {len(structure)} sites, unchanged cell; host {host}.")
    print(f"Job directory: {destination}")
    print(f"On the cluster: cd '{destination}'; sbatch run_sqs.sh")
    print("Final structure: runs/slurm_<jobid>_seed_<seed>/POSCAR_sqs")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare fixed-cell ATAT SQS inputs and a one-seed, one-CPU Slurm job."
    )
    parser.add_argument("poscar", type=Path, help="Input POSCAR/CONTCAR; cell and sites stay fixed")
    parser.add_argument("--solute", nargs="+", action="extend", required=True,
                        metavar="ELEMENT=COUNT",
                        help="One or more element=count replacements, e.g. Nb=1 Fe=1; "
                             "repeat --solute to append more distinct elements. "
                             "Counts must be positive integers; duplicate elements are rejected")
    parser.add_argument("--host", help="Element to replace; inferred only for single-element inputs")
    parser.add_argument("-o", "--output",
                        help="New job directory; default/bare name is beside input: SQS_<formula>")
    parser.add_argument("--seed", type=int, default=101, help="Default random seed (default: 101)")
    parser.add_argument("--steps", type=int, default=200000, help="Maximum MC steps (default: 200000)")
    parser.add_argument("--pair-cutoff", type=float, default=4.8, help="Pair cutoff in Angstrom (default: 4.8)")
    parser.add_argument("--triplet-cutoff", type=float, default=3.3,
                        help="Triplet cutoff in Angstrom (default: 3.3)")
    parser.add_argument("--corr-tol", type=float, default=1e-6,
                        help="Correlation matching tolerance (default: 1e-6)")
    parser.add_argument("--site-tol", type=float, default=0.002,
                        help="Maximum site mapping residual in Angstrom (default: 0.002)")
    parser.add_argument("--partition", default="cpu1", help="Slurm partition (default: cpu1)")
    args = parser.parse_args()
    try:
        prepare(args)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
