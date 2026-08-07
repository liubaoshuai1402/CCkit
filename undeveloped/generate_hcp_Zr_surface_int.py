# CCkit 功能说明：
# 实验性脚本：生成 HCP Zr 表面及其间隙原子结构。
import numpy as np


pentahedron = {
    "Zr_CommonVertex": np.array([-0.5, 0.16667, 0.36795]),
    "Zr_CommonEdge_FourAtomsPlane": np.array([0.5, 0.16667, 0.36795]),
    "Zr_CommonEdge_TwoAtomsLine": np.array([0.0,0.33333,0.45994]),
    "Zr_Exclusive_FourAtomsPlane": np.array([0,-0.33333,0.36795]),
    "Zr_Exclusive_TwoAtomsLine": np.array([-0.5, -0.16667, 0.45994])
}
tetrahedron = {
    "Zr_CommonVertex": np.array([-0.5, 0.16667, 0.36795]),
    "Zr_CommonEdge_FourAtomsPlane": np.array([0.5, 0.16667, 0.36795]),
    "Zr_CommonEdge_TwoAtomsLine": np.array([0.0,0.33333,0.45994]),
    "Zr_Exclusive_FourAtomsPlane": np.array([0.0,0.66667,0.36975])
}

# define hcp-Zr 0001 surface lattice
a = 3.18520
b = 5.51700
c = 27.7745
adup = 3
bdup = 2
cdup = 1

# define the interstitial
# Ref: https://www.sciencedirect.com/science/article/pii/S0022311512002899
# The all positions are within a conventional orthogonal cell:
# 1.0
# a*3 0 0
# 0 b*2 0
# 0 0 c
# Zr
# 12
# d
#0.000000000         0.666670000         0.000000000
#0.500000000         0.166670000         0.000000000
#0.000000000         0.666670000         0.183970000
#0.500000000         0.166670000         0.183970000
#0.000000000         0.666670000         0.367950000
#0.500000000         0.166670000         0.367950000
#0.000000000         0.333330000         0.091990000
#0.500000000         0.833330000         0.091990000
#0.000000000         0.333330000         0.275960000
#0.500000000         0.833330000         0.275960000
#0.000000000         0.333330000         0.459940000
#0.500000000         0.833330000         0.459940000

O_pos  = (pentahedron["Zr_CommonEdge_FourAtomsPlane"] + pentahedron["Zr_Exclusive_TwoAtomsLine"])/2
BO_pos = (pentahedron["Zr_CommonVertex"] + pentahedron["Zr_CommonEdge_FourAtomsPlane"] + pentahedron["Zr_Exclusive_FourAtomsPlane"])/3
S_pos  = [] # special for it changes other atom's coordination
BS_pos = [] # special for it changes other atom's coordination
C_pos  = (pentahedron["Zr_CommonEdge_FourAtomsPlane"] + pentahedron["Zr_CommonEdge_TwoAtomsLine"])/2
BC_pos = (pentahedron["Zr_CommonVertex"] + pentahedron["Zr_CommonEdge_FourAtomsPlane"])/2
T_pos  = (tetrahedron['Zr_CommonVertex']+ tetrahedron['Zr_CommonEdge_FourAtomsPlane']+ tetrahedron['Zr_CommonEdge_TwoAtomsLine']+ tetrahedron["Zr_Exclusive_FourAtomsPlane"])/4
BT_pos = (tetrahedron['Zr_CommonVertex']+ tetrahedron['Zr_CommonEdge_FourAtomsPlane']+ tetrahedron['Zr_Exclusive_FourAtomsPlane'])/3

int_poses = [O_pos, BO_pos, S_pos, BS_pos, C_pos, BC_pos, T_pos, BT_pos]
int_pos_names = ["O_pos", "BO_pos", "S_pos", "BS_pos", "C_pos", "BC_pos", "T_pos", "BT_pos"]


# write POSCAR_with_int
for int_pos, int_pos_name in zip(int_poses, int_pos_names):
    if list(int_pos):
        with open(f"POSCAR_{int_pos_name}", "w") as f:
            f.write(f"HCP Zr 0001 surface{adup}x{bdup}x{cdup} with {int_pos_name}\n")
            f.write("1.0 \n")
            f.write(f"{a*adup} 0.0 0.0 \n")
            f.write(f"0.0 {b*bdup} 0.0 \n")
            f.write(f"0.0 0.0 {c*cdup} \n")
            f.write("Zr\n")
            f.write(f"{12*adup*bdup*cdup+1} \n")
            f.write("Direct \n")
            for i in range(0, adup):
                for j in range(0, bdup):
                    for k in range(0, cdup):
                        f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                        f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.18397/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.18397/cdup+k/cdup} \n")
                        f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.36795/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.36795/cdup+k/cdup} \n")
                        f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.09199/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.09199/cdup+k/cdup} \n")
                        f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.27596/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.27596/cdup+k/cdup} \n")
                        f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.45994/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.45994/cdup+k/cdup} \n")
            f.write(f"{int_pos[0]/adup} {int_pos[1]/bdup} {int_pos[2]/cdup} \n")
    else:
        with open(f"POSCAR_{int_pos_name}", "w") as f:
            f.write(f"HCP Zr 0001 surface{adup}x{bdup}x{cdup} with {int_pos_name}\n")
            f.write("1.0 \n")
            f.write(f"{a*adup} 0.0 0.0 \n")
            f.write(f"0.0 {b*bdup} 0.0 \n")
            f.write(f"0.0 0.0 {c*cdup} \n")
            f.write("Zr\n")
            f.write(f"{12*adup*bdup*cdup+1} \n")
            f.write("Direct \n")
            for i in range(0, adup):
                for j in range(0, bdup):
                    for k in range(0, cdup):
                        if not (i==0 and j==0 and k==0):
                            f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.18397/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.18397/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.36795/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.36795/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.09199/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.09199/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.27596/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.27596/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.45994/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.45994/cdup+k/cdup} \n")
                        else:
                            f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.18397/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.166667/bdup+j/bdup} {0.18397/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.666667/bdup+j/bdup} {0.36795/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.09199/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.09199/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.27596/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.27596/cdup+k/cdup} \n")
                            f.write(f"{0.0/adup+i/adup} {0.333333/bdup+j/bdup} {0.45994/cdup+k/cdup} \n")
                            f.write(f"{0.5/adup+i/adup} {0.833333/bdup+j/bdup} {0.45994/cdup+k/cdup} \n")
            if int_pos_name == "S_pos":
                f.write(f"{0.5} {0.166667} {0.36795+0.03099/cdup} \n")
                f.write(f"{0.5} {0.166667} {0.36795-0.03099/cdup} \n")
            else:
                f.write(f"{0.5+1/3/adup} {0.166667} {0.36795} \n")
                f.write(f"{0.5-1/3/adup} {0.166667} {0.36795} \n")
    print(f"POSCAR_{int_pos_name} file written.")
