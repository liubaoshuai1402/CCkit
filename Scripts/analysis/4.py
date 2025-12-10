from pymatgen.core import Structure
import numpy as np
from ase.io import read 
from pymatgen.io.ase import AseAtomsAdaptor

# ==== 参数设置 ====
input_file = '../relaxed/ysz_42_100_new/3.xyz'           # 你的结构文件

structure = read(input_file)
structure = AseAtomsAdaptor.get_structure(structure)
bondedH = 0
interstitialH = 0
transitiveH = 0



for i, site in enumerate(structure):
    if site.specie.symbol != "H":
        continue  # 跳过非H原子
    count = 0
    Hneighbors = structure.get_neighbors(site,1.2)
    for Hneighbor in Hneighbors:
        if Hneighbor.specie.symbol == 'O':
            bondedH = bondedH + 1
            count = count + 1
            break
    if count == 1:
        continue
    Hneighbors = structure.get_neighbors(site,2.0)
    if Hneighbors == []:
        interstitialH = interstitialH + 1
        continue
    if count == 0:
        transitiveH = transitiveH + 1
print(bondedH)
print(interstitialH)
print(transitiveH)



