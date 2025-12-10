from ase.io import read,write
import numpy as np
from hiphive.structure_generation import generate_mc_rattled_structures
import os

db = read('CONTCAR')
db = [db, db, db]
rng = np.random.default_rng(seed=1214)
set1 = []
for at in db:
    set1.extend(generate_mc_rattled_structures(at,1,rattle_std=0.02,d_min=1.0,seed=rng.integers(1,10**9)))

write('test.xyz',set1)

