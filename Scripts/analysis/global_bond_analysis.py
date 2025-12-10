#统计A-B键分布
import argparse
import numpy as np
from ase.io import read 
from pymatgen.io.ase import AseAtomsAdaptor
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


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
        np.savetxt("Allbonds_KDE_global.txt", output_array, header="x y", fmt="%.6f")
    elif title == 'longbonds':
        np.savetxt("Longbonds_KDE_global.txt", output_array, header="x y", fmt="%.6f")
    elif title == 'shortbonds':
        np.savetxt("Shortbonds_KDE_global.txt", output_array, header="x y", fmt="%.6f")

    # 绘图
    plt.figure(figsize=(8, 5))
    plt.plot(x_grid, y, color="blue")

    plt.xlabel("Bond Length")
    plt.ylabel("KDE Density")
    if title == 'bonds':
        plt.title("All A-B Bond Lengths Distribution_global")
    elif title == 'longbonds':
        plt.title("Long A-B Bond Lengths Distribution_global")
    elif title == 'shortbonds':
        plt.title("Short A-B Bond Lengths Distribution_global")
    plt.grid(True)
    # 保存图片
    if title == 'bonds':
        plt.savefig("Allbonds_dis_global.png", dpi=300, bbox_inches='tight')
    elif title == 'longbonds':
        plt.savefig("Longbonds_dis_global.png", dpi=300, bbox_inches='tight')
    elif title == 'shortbonds':
        plt.savefig("Shortbonds_dis_global.png", dpi=300, bbox_inches='tight')

def global_bond_distribution_analysis(structs,elementA,elementB,cutoff,plt=False):
    longbonds = []
    shortbonds = []
    bonds = []
    for struct in structs:
        struct = AseAtomsAdaptor.get_structure(struct)

        # 遍历所有 A 原子
        for i, site in enumerate(struct):
            if site.specie.symbol != elementA:
                continue  # 跳过非 A 原子

            # 搜索邻居：为了确保找到所有可能 B 原子，用一个稍大的 cutoff，例如 2.8 Å
            neighbors = struct.get_neighbors(site, r=cutoff)

            for neigh in neighbors:
                if neigh.specie.symbol == elementB:
                    distance = neigh.distance(site)
                    bonds.append(distance)
                    if 1.80 <= distance <= 2.20:
                        shortbonds.append(distance)
                    if 2.20 < distance <= 2.60:
                        longbonds.append(distance)
    np.savetxt('bands_dis_global.txt',bonds)
    np.savetxt('longbands_dis_global.txt',longbonds)
    np.savetxt('shortbands_dis_global.txt',shortbonds)
    if plt:
        plt_KDE(bonds, 'bonds')
        plt_KDE(longbonds, 'longbonds')
        plt_KDE(shortbonds, 'shortbonds')


def main():
    #告诉python要解析命令行
    parser = argparse.ArgumentParser(description="Analyze the A-B bond distribution")
    #如何解析命令行
    parser.add_argument("input", type=str, help="Input file, single structure or trajectory")
    parser.add_argument("elementA", type=str, help="elementA")
    parser.add_argument("elementB", type=str, help="elementB")
    parser.add_argument("cutoff", type=float, help="cutoff of A-B bond")
    parser.add_argument('--plt',action="store_true",help="If set, plot KDA")
    #将解析结果储存
    args = parser.parse_args()
    
    structs = read(args.input,':')
    global_bond_distribution_analysis(structs, args.elementA, args.elementB, args.cutoff, args.plt)
    print('bands_dis.txt, longbands_dis.txt, shortbands_dis.txt are saved')


if __name__ == "__main__":
    main()