#! /home/meihj/atomate/atomate_env/bin/python
# CCkit 功能说明：
# 实验性脚本：生成 HCP 晶体中的间隙原子结构。
# coding=utf-8
'''
Author: Haojie Mei
Date: 2023-03-14 08:49:38
LastEditTime: 2023-03-14 15:27:57
LastEditors: Haojie Mei
FilePath: /meihj/tmp/ZrSn/0-dft/12-int/generate_hcp_int.py
Github: https://github.com/meihaojie
Description: generate HCP structure with interstitial atoms
'''

# define HCP lattice
a = 3.2307576260490896
c = 5.1657955138452420
element = "Zr"
adup = 2
bdup = 4
cdup = 2

# define the interstitial
# Ref: https://www.sciencedirect.com/science/article/pii/S0022311512002899
# The all positions are within a conventional orthogonal cell:
# 1.0
# a*3**0.5 0 0
# 0        a 0
# 0        0 c
# element
# 4
# d
# 0 0 0
# 0.5 0.5 0
# 1/6 0.5 0.5
# 2/3 0 0.5
O_pos  = [2/6, 0, 1/4] # changed
BO_pos = [2/6, 0, 0]
S_pos  = [] # special for it changes other atom's coordination
BS_pos = [] # special for it changes other atom's coordination
C_pos  = [1/12, 1/4, 1/4]
BC_pos = [0, 1/2, 0]
T_pos  = [1/6, 1/2, 1/8] # https://zhuanlan.zhihu.com/p/598067515
BT_pos = [1/6, 1/2, 0]

int_poses = [O_pos, BO_pos, S_pos, BS_pos, C_pos, BC_pos, T_pos, BT_pos]
int_pos_names = ["O_pos", "BO_pos", "S_pos", "BS_pos", "C_pos", "BC_pos", "T_pos", "BT_pos"]

# write POSCAR_with_int
for int_pos, int_pos_name in zip(int_poses, int_pos_names):
    if int_pos:
        with open(f"POSCAR_{int_pos_name}", "w") as f:
            f.write(f"HCP {element} {adup}x{bdup}x{cdup} with {int_pos_name}: {int_pos} \n")
            f.write("1.0 \n")
            f.write(f"{a*3**0.5*adup} 0.0 0.0 \n")
            f.write(f"0.0 {a*bdup} 0.0 \n")
            f.write(f"0.0 0.0 {c*cdup} \n")
            f.write(f"{element} \n")
            f.write(f"{4*adup*bdup*cdup+1} \n")
            f.write("Direct \n")
            for i in range(0, adup):
                for j in range(0, bdup):
                    for k in range(0, cdup):
                        f.write(f"{0.0/adup+i/adup} {0.0/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.5/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                        f.write(f"{1/6/adup+i/adup} {0.5/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
                        f.write(f"{2/3/adup+i/adup} {0.0/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
            f.write(f"{int_pos[0]/adup} {int_pos[1]/bdup} {int_pos[2]/cdup} \n")
    else:
        with open(f"POSCAR_{int_pos_name}", "w") as f:
            f.write(f"HCP {element} {adup}x{bdup}x{cdup} with {int_pos_name}: {int_pos} \n")
            f.write("1.0 \n")
            f.write(f"{a*3**0.5*adup} 0.0 0.0 \n")
            f.write(f"0.0 {a*bdup} 0.0 \n")
            f.write(f"0.0 0.0 {c*cdup} \n")
            f.write(f"{element} \n")
            f.write(f"{4*adup*bdup*cdup+1} \n")
            f.write("Direct \n")
            for i in range(0, adup):
                for j in range(0, bdup):
                    for k in range(0, cdup):
                        if not (i==0 and j==0 and k==0):
                            f.write(f"{0.0/adup+i/adup} {0.0/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.5/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{1/6/adup+i/adup} {0.5/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
                            f.write(f"{2/3/adup+i/adup} {0.0/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
                        else:
                            f.write(f"{0.5/adup+i/adup} {0.5/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{1/6/adup+i/adup} {0.5/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
                            f.write(f"{2/3/adup+i/adup} {0.0/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
            if int_pos_name == "S_pos":
                f.write(f"{0.0} {0.0} {1/6/cdup} \n")
                f.write(f"{0.0} {0.0} {1-1/6/cdup} \n")
            else:
                f.write(f"{0.0} {1/3/bdup} {0.0} \n")
                f.write(f"{0.0} {1-1/3/bdup} {0.0} \n")
    print(f"POSCAR_{int_pos_name} file written.")
