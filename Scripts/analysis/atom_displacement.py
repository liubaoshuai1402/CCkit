from ase.io import read,write
import argparse

def calculate_atom_displacement(original, displaced):
    """
    Calculate the displacement of atoms between the original and displaced structures.

    Parameters:
    original (ase.Atoms): The original structure.
    displaced (ase.Atoms): The displaced structure.

    Returns:
    list: A list of displacement vectors for each atom.
    """
    if len(original) != len(displaced):
        raise ValueError("Original and displaced structures must have the same number of atoms.")

    displacements = []
    for orig_atom, disp_atom in zip(original, displaced):
        displacement = np.linalg.norm(disp_atom.position - orig_atom.position)
        displacements.append(displacement)

    return displacements