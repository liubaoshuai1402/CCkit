import argparse
from ase.io import read,write
import numpy as np
from hiphive.structure_generation import generate_mc_rattled_structures
import os

#施加轴向应变
def apply_uniaxial_strain(prim, strain_limt):
    strains = np.random.uniform(*strain_limt, (3, ))
    atoms = prim.copy()
    cell_new = prim.cell[:] * (1 + strains)
    atoms.set_cell(cell_new, scale_atoms=True)
    return atoms

#施加仿射应变
def apply_affine_strain(prim, strain_limt):
    R = np.random.uniform(*strain_limt, (3, 3))
    M = np.eye(3) + R
    atoms = prim.copy()
    cell_new = M @ atoms.cell[:]
    atoms.set_cell(cell_new, scale_atoms=True)
    return atoms

#采用MC方法微扰结构
def rattled_strain_structure(prim, strain_limt, N1, N2, M, rattle_std, n_iter, d_min):
    strain_structures = []
    rattled_strain_structures=[]
    strain_limt = [-strain_limt,strain_limt]

    for it in range(N1):
        strain_structures.append(apply_uniaxial_strain(prim, strain_limt))
    for it in range(N2): 
        strain_structures.append(apply_affine_strain(prim, strain_limt))
  
    for at in strain_structures:
        rattled_strain_structures.extend(generate_mc_rattled_structures(atoms=at, n_structures=M, rattle_std=rattle_std, seed=np.random.randint(1, 10**9), n_iter=n_iter, d_min=d_min))
    return rattled_strain_structures

def main():
    parser = argparse.ArgumentParser(description="Random strain structure generator.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("strain_limt", type=float, help="max range of strain, please give one positive float, for example,0.5 will be taken as [-0.5,0.5]")
    parser.add_argument("N1", type=int, help="Number of uniaxial_strain structures")
    parser.add_argument("N2", type=int, help="Number of affine_strain structures")
    parser.add_argument("M", type=int, help="Number of rattled structures for each strain structures")
    
    parser.add_argument("--rattle", type=float, default=0.02, help="rattle amplitude (default 0.02): larger rattle, larger displacements")
    parser.add_argument("--iter", type=int, default=10, help="int number of Monte Carlo cycles (default 10): larger iter, larger displacements")
    parser.add_argument("--dmin", type=float, default=0.7, help="Min interatomic distance allowed: smaller dmin, closer the atoms are allowed to get, default = 0.7")
    parser.add_argument("--seed", type=int, default=1214, help="Random seed,default = 1214")
    parser.add_argument("-o", "--output", type=str, default="rattled_strain_structures.xyz", help="Output file,default: rattled_strain_structures.xyz")

    args = parser.parse_args()

    #读取结构，设置seed
    prims = read(args.input,':')
    np.random.seed(args.seed)

    #对给定的结构和轨迹施加应变和扰动
    output_struct = []
    for prim in prims:
        output_struct.extend(rattled_strain_structure(prim, args.strain_limt, args.N1, args.N2, args.M, args.rattle, args.iter, args.dmin))
    write(args.output,output_struct)
    
    print(f"Generated {len(prims) * (args.N1 + args.N2) * args.M} structures → {args.output}")

if __name__ == "__main__":
    main()





    