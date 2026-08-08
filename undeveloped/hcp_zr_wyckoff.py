"""Generate hcp Zr with O, H, Ti and C on selected Wyckoff positions.

Space group 194 is P6_3/mmc. The structure uses Zr-2c, O-2a, H-2d,
Ti-4f and C-6g. pyxtal expands each representative coordinate with the
symmetry operations of the corresponding Wyckoff position.
"""

import sys
from pathlib import Path
from typing import Union

# Make the script independent of the directory from which it is launched.
_ENV_SITE_PACKAGES = Path(sys.prefix) / "Lib" / "site-packages"
if str(_ENV_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(_ENV_SITE_PACKAGES))

from pyxtal import pyxtal
from pyxtal.lattice import Lattice


def build_hcp_zr(
    a: float = 3.231,
    c: float = 5.147,
    output: Union[str, Path] = "zr_hcp.cif",
) -> pyxtal:
    """Build hcp alpha-Zr with the requested atoms and write a CIF file.

    Args:
        a: Hexagonal basal-plane lattice constant in Angstrom.
        c: Hexagonal lattice constant in Angstrom.
        output: Output CIF path.

    Returns:
        The generated pyxtal structure.
    """
    if a <= 0 or c <= 0:
        raise ValueError("a and c must be positive")

    structure = pyxtal()
    lattice = Lattice.from_para(
        a, a, c, 90.0, 90.0, 120.0, ltype="hexagonal"
    )

    # P6_3/mmc (No. 194): Zr-2c, O-2a, H-2d, Ti-4f and C-6g.
    structure.build(
        group=194,
        species=["Zr", "O", "H", "Ti", "C", "B", "Cr"],
        numIons=[2, 2, 2, 4, 6, 2, 6],
        lattice=lattice,
        sites=[
            [{"2c": [1.0 / 3.0, 2.0 / 3.0, 1.0 / 4.0]}],
            [{"2a": [0.0, 0.0, 0.0]}],
            [{"2d": [1.0 / 3.0, 2.0 / 3.0, 3.0 / 4.0]}],
            [{"4f": [2.0 / 3.0, 1.0 / 3.0, 0.125]}],
            [{"6g": [0.5, 0.0, 0.0]}],
            [{"2b": [0.0, 0.0, 1.0 / 4.0]}],
            [{"6h": [1/3, 1/6, 0.25]}]
        ],
    )
    structure.to_file(str(output), fmt="cif")

    assert structure.group.number == 194
    assert list(structure.numIons) == [2, 2, 2, 4, 6, 2, 6]
    assert [site.wp.get_label() for site in structure.atom_sites] == [
        "2c", "2a", "2d", "4f", "6g", "2b", "6h"
    ]
    return structure


if __name__ == "__main__":
    output_path = Path("Zr_hcp_O_H_Ti_C_B_Cr.cif")
    xtal = build_hcp_zr(output=output_path)
    print(f"Wrote {output_path.resolve()}")
    print(xtal)
