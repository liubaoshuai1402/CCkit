# CCkit 功能说明：
# 按照原子类型对结构或轨迹进行分组并输出分组结果。
#group according to atom type
from ase.io import read,write
import numpy as np
import argparse

def group_type(struct,):
atoms = read('POSCAR_perturbed_0')
group = []
for at in atoms:
    if at.symbol == 'H':
        group.append(0)
    if at.symbol == 'O':
        group.append(1)
    if at.symbol == 'Zr':
        group.append(2)
    if at.symbol == 'Y':
        group.append(3)
atoms.arrays['group'] = np.array(group)
write('yourfile_with_flags.xyz', atoms)

def main():
    parser = argparse.ArgumentParser(description="get average stress from thermo.out and write to stress.txt")

    parser.add_argument("--nptdir", type=str, default='.',help="the directory run npt, default is .")

    args = parser.parse_args()

    stress_temp = average_stress(args.nptdir)
    np.savetxt(os.path.join(args.nptdir,'stress.txt'),stress_temp)

if __name__ == "__main__":
    main()
