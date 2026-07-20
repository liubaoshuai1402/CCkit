# ==========================================================
# Generate vacancy migration NEB initial and final structures
# ==========================================================
#
# This script is used to construct the initial and final
# structures for vacancy migration NEB calculations.
#
# In NEB calculations, the initial and final structures must
# have the same number of atoms and identical atom ordering.
# However, directly removing atoms at different vacancy sites
# will change atomic indices and break the atom correspondence
# between the two structures.
#
# This script solves this problem by:
#
# 1. Removing the two atoms involved in vacancy migration from
#    the perfect structure to generate a common atomic backbone.
#
# 2. Inserting the atom from the final vacancy site into the
#    backbone to generate the initial NEB structure.
#
# 3. Inserting the atom from the initial vacancy site into the
#    same position to generate the final NEB structure.
#
# The generated POSCAR0 and POSCAR1 therefore have:
# - identical atom numbers
# - identical atom ordering
# - consistent atomic correspondence
#
# This guarantees a physically meaningful interpolation path
# for vacancy migration NEB calculations in VASP.
#
# Example:
# python script.py POSCAR 12 35 -e O
#
# where:
# 12 : atom index removed in initial state
# 35 : atom index removed in final state
# ==========================================================

import argparse
from ase.io import read,write

def insert_atom(atoms,atom,index):
    new=atoms[:index]
    new.append(atom)
    new.extend(atoms[index:])
    return new

def main():
    parser=argparse.ArgumentParser(description="Generate NEB structures for vacancy migration.")
    parser.add_argument("filename",help="Input perfect POSCAR")
    parser.add_argument("initial",type=int,help="Atom index removed in initial state")
    parser.add_argument("final",type=int,help="Atom index removed in final state")
    parser.add_argument("-e","--element",default="O",help="Vacancy element (default: O)")
    parser.add_argument("-o0",default="POSCAR0",help="Output initial structure")
    parser.add_argument("-o1",default="POSCAR1",help="Output final structure")
    args=parser.parse_args()

    atoms=read(args.filename)
    vac_distance = atoms.get_distance(args.initial,args.final,mic=True)
    n=len(atoms)

    if args.initial<0 or args.initial>=n:
        raise ValueError("Initial atom index out of range.")
    if args.final<0 or args.final>=n:
        raise ValueError("Final atom index out of range.")
    if args.initial==args.final:
        raise ValueError("Initial and final atom indices cannot be the same.")
    if atoms[args.initial].symbol!=args.element:
        raise ValueError(f"Atom {args.initial} is not {args.element}.")
    if atoms[args.final].symbol!=args.element:
        raise ValueError(f"Atom {args.final} is not {args.element}.")

    backbone=atoms[[i for i in range(n) if i not in (args.initial,args.final)]]

    indices=backbone.symbols.indices()
    if args.element not in indices:
        raise ValueError(f"No {args.element} atoms remain in backbone.")

    insert_index=max(indices[args.element])+1

    poscar0=insert_atom(backbone,atoms[args.final],insert_index)
    poscar1=insert_atom(backbone,atoms[args.initial],insert_index)

    write(args.o0,poscar0,format="vasp",vasp5=True,direct=True,sort=False)
    write(args.o1,poscar1,format="vasp",vasp5=True,direct=True,sort=False)

    print("========== NEB Alignment ==========")
    print(f"Input structure : {args.filename}")
    print(f"Vacancy element : {args.element}")
    print(f"Initial vacancy : atom {args.initial}")
    print(f"Final vacancy   : atom {args.final}")
    print(f"Vacancy distance: {vac_distance:.4f} Å")
    print(f"Output initial  : {args.o0}")
    print(f"Output final    : {args.o1}")
    print("===================================")

if __name__=="__main__":
    main()