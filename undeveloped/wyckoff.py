from pyxtal import pyxtal

xtal = pyxtal()
xtal.from_seed(
    r"zr_hcp_O_H_Ti_C_B_Cr.cif",
    backend="pymatgen",
)

print(f"空间群: {xtal.group.number} {xtal.group.symbol}")

for site in xtal.atom_sites:
    print(
        f"元素: {site.specie:>2s}, "
        f"Wyckoff: {site.wp.get_label():>3s}, "
        f"重数: {site.wp.multiplicity}, "
        f"代表坐标: {site.position}"
    )