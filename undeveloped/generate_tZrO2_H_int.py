# CCkit 功能说明：
# 实验性脚本：生成四方 ZrO2 中的氢间隙结构。
# define t-ZrO2 pseudoflurite lattice
a = 5.0954999924
c = 5.2217998505
element = "Zr"
adup = 2
bdup = 2
cdup = 2

# define the interstitial
# The all positions are within a pseudoflurite cell:
# 1.0
# a 0 0
# 0 a 0
# 0 0 c
# element Zr O
# 12
# d
#0.000000000         0.000000000         0.000000000 Zr
#0.500000000         0.500000000         0.000000000 Zr
#0.000000000         0.500000000         0.500000000 Zr
#0.500000000         0.000000000         0.500000000 Zr
#0.250000000         0.250000000         0.301730000 O
#0.750000000         0.750000000         0.301730000 O
#0.250000000         0.250000000         0.801730000 O
#0.750000000         0.750000000         0.801730000 O
#0.250000000         0.750000000         0.698270000 O
#0.750000000         0.250000000         0.698270000 O
#0.250000000         0.750000000         0.198270000 O
#0.750000000         0.250000000         0.198270000 O

atom_numbers = {"Zr": 4*adup*bdup*cdup, "O": 8*adup*bdup*cdup}

#about definiton of int atoms https://www.sciopen.com/article/10.26599/JAC.2025.9221099
CC_pos = [0.5, 0.5, 0.5]                          #6Zr8O cage center
SAC_pos = [0.25, 0.25, (0.81730+0.301730)/2]      #Surface A center  
SBC_pos = [0.5, 0.25, (0.817230+0.198270)/2]      #Surface B center
B_pos = [0.64554,0.35446,0.5722]                  #bonded position

int_poses = [CC_pos, SAC_pos, SBC_pos, B_pos]
int_pos_names = ["CC_pos", "SAC_pos", "SBC_pos", "B_pos"]

# write POSCAR_with_int
for int_pos, int_pos_name in zip(int_poses, int_pos_names):
    if int_pos:
        with open(f"POSCAR_{int_pos_name}", "w") as f:
            f.write(f"pseudoflurite t-ZrO2 {adup}x{bdup}x{cdup} with {int_pos_name}\n")
            f.write("1.0 \n")
            f.write(f"{a*adup} 0.0 0.0 \n")
            f.write(f"0.0 {a*bdup} 0.0 \n")
            f.write(f"0.0 0.0 {c*cdup} \n")
            f.write("Zr O H\n")
            f.write(f"{atom_numbers['Zr']} {atom_numbers['O']} 1\n")
            f.write("Direct \n")
            #write Zr atoms
            for i in range(0, adup):
                for j in range(0, bdup):
                    for k in range(0, cdup):
                        f.write(f"{0.0/adup+i/adup} {0.0/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.5/bdup+j/bdup} {0.0/cdup+k/cdup} \n")
                        f.write(f"{0.0/adup+i/adup} {0.5/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
                        f.write(f"{0.5/adup+i/adup} {0.0/bdup+j/bdup} {0.5/cdup+k/cdup} \n")
            #write O atoms
            for i in range(0, adup):
                for j in range(0, bdup):
                    for k in range(0, cdup):
                        f.write(f"{0.25/adup+i/adup} {0.25/bdup+j/bdup} {(0.301730)/cdup+k/cdup} \n")
                        f.write(f"{0.75/adup+i/adup} {0.75/bdup+j/bdup} {(0.301730)/cdup+k/cdup} \n")
                        f.write(f"{0.25/adup+i/adup} {0.25/bdup+j/bdup} {(0.801730)/cdup+k/cdup} \n")
                        f.write(f"{0.75/adup+i/adup} {0.75/bdup+j/bdup} {(0.801730)/cdup+k/cdup} \n")
                        f.write(f"{0.25/adup+i/adup} {0.75/bdup+j/bdup} {(0.698270)/cdup+k/cdup} \n")
                        f.write(f"{0.75/adup+i/adup} {0.25/bdup+j/bdup} {(0.698270)/cdup+k/cdup} \n")
                        f.write(f"{0.25/adup+i/adup} {0.75/bdup+j/bdup} {(0.198270)/cdup+k/cdup} \n")
                        f.write(f"{0.75/adup+i/adup} {0.25/bdup+j/bdup} {(0.198270)/cdup+k/cdup} \n")
            f.write(f"{int_pos[0]/adup} {int_pos[1]/bdup} {int_pos[2]/cdup} \n")
    print(f"POSCAR_{int_pos_name} file written.")





