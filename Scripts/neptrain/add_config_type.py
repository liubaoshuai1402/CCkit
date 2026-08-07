"""Add an ASE/extended-XYZ Config_type label to structures or trajectories."""

# CCkit 功能说明：
# 为 ASE 支持的结构或轨迹添加统一的 Config_type 标签。
import argparse
from pathlib import Path

from ase.io import read, write


def default_output_path(input_path):
    path = Path(input_path)
    return path.with_name(f"{path.stem}_config_type.extxyz")


def main():
    parser = argparse.ArgumentParser(
        description="Add the same Config_type label to every configuration in a file."
    )
    parser.add_argument("input", help="Input structure or trajectory file supported by ASE")
    parser.add_argument("config_type", help="Value to assign to the Config_type label")
    parser.add_argument(
        "--slice",
        default=":",
        help="ASE index/slice selecting configurations (default: all configurations)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output extended-XYZ file (default: <input>_config_type.extxyz)",
    )
    args = parser.parse_args()

    output = args.output or str(default_output_path(args.input))
    configurations = read(args.input, index=args.slice)
    if not isinstance(configurations, list):
        configurations = [configurations]

    if not configurations:
        raise ValueError("No configurations were read from the input file")

    for atoms in configurations:
        atoms.info["Config_type"] = args.config_type

    write(output, configurations, format="extxyz")
    print(f"Labeled {len(configurations)} configuration(s) with Config_type={args.config_type!r}")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
