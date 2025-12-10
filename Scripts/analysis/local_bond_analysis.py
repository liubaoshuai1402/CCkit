#统计了氢原子附近的A-B键分布
import numpy as np
from ase.io import read 
from pymatgen.io.ase import AseAtomsAdaptor
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import argparse

def plt_KDE(bond_dis,title):
    # 全局字体设置为 Arial
    plt.rcParams["font.family"] = "Arial"

    # -----------------------------
    # 加载数据
    # -----------------------------
    data = np.array(bond_dis)

    # KDE 计算
    kde = gaussian_kde(data)

    # 横坐标范围：覆盖两组数据
    xmin = data.min() - 0.2
    xmax = data.max() + 0.2
    x_grid = np.linspace(xmin, xmax, 500)

    # KDE 值
    y = kde(x_grid)
    
    #输出KDE数据
    output_array = np.column_stack((x_grid, y))
    if title == 'bonds':
        np.savetxt("Allbonds_KDE_local.txt", output_array, header="x y", fmt="%.6f")
    elif title == 'longbonds':
        np.savetxt("Longbonds_KDE_local.txt", output_array, header="x y", fmt="%.6f")
    elif title == 'shortbonds':
        np.savetxt("Shortbonds_KDE_local.txt", output_array, header="x y", fmt="%.6f")

    # 绘图
    plt.figure(figsize=(8, 5))
    plt.plot(x_grid, y, color="blue")

    plt.xlabel("Bond Length")
    plt.ylabel("KDE Density")
    if title == 'bonds':
        plt.title("All A-B Bond Lengths Distribution_local")
    elif title == 'longbonds':
        plt.title("Long A-B Bond Lengths Distribution_local")
    elif title == 'shortbonds':
        plt.title("Short A-B Bond Lengths Distribution_local")
    plt.grid(True)
    # 保存图片
    if title == 'bonds':
        plt.savefig("Allbonds_dis_local.png", dpi=300, bbox_inches='tight')
    elif title == 'longbonds':
        plt.savefig("Longbonds_dis_local.png", dpi=300, bbox_inches='tight')
    elif title == 'shortbonds':
        plt.savefig("Shortbonds_dis_local.png", dpi=300, bbox_inches='tight')
    


def local_bond_distribution_analysis(structs,elementA,elementB,cutoff1,cutoff2,plt=False):

    for struct in structs:
        struct = AseAtomsAdaptor.get_structure(struct)
        longbonds = []
        shortbonds = []
        bonds = []
        # 遍历所有 H 原子
        for i, site in enumerate(struct):
            if site.specie.symbol != "H":
                continue  # 跳过非H原子

            # 搜索 H 原子的邻居A 原子
            H_neighbors = struct.get_neighbors(site, cutoff1)

            for H_neigh in H_neighbors:
                if H_neigh.specie.symbol == elementA:
                    #统计A 原子的邻居B 原子
                    A_neighbors = struct.get_neighbors(H_neigh, cutoff2)
                    for A_neigh in A_neighbors:
                        if A_neigh.specie.symbol == elementB:
                            distance = A_neigh.distance(H_neigh)
                            bonds.append(distance)
                            #长短键
                            if 1.80 <= distance <= 2.20:
                                shortbonds.append(distance)
                            if 2.20 < distance <= 2.60:
                                longbonds.append(distance)
    np.savetxt('bands_dis_local.txt',bonds)
    np.savetxt('longbands_dis_local.txt',longbonds)
    np.savetxt('shortbands_dis_local.txt',shortbonds)
    if plt:
        plt_KDE(bonds, 'bonds')
        plt_KDE(longbonds, 'longbonds')
        plt_KDE(shortbonds, 'shortbonds')


def main():
    parser = argparse.ArgumentParser(description="Analyze the A-B bond distribution")

    parser.add_argument("input", type=str, help="Input file, single structure or trajectory")
    parser.add_argument("elementA", type=str, help="elementA, for example O")
    parser.add_argument("elementB", type=str, help="elementB, for example Zr")
    parser.add_argument("cutoff1", type=float, help="cutoff of H-A distance")
    parser.add_argument("cutoff2", type=float, help="cutoff of A-B bond")
    parser.add_argument('--plt',action="store_true",help="If set, plot KDA")
    
    args = parser.parse_args()
    structs = read(args.input,':')
    local_bond_distribution_analysis(structs, args.elementA, args.elementB, args.cutoff1, args.cutoff2, args.plt)
    print('bands_dis.txt, longbands_dis.txt, shortbands_dis.txt are saved')

if __name__ == "__main__":
    main()