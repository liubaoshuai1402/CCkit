# CCkit 功能说明：
# 实验性脚本：根据结构或数据特征对对象进行分类。
import os
import shutil
import numpy as np
import pandas as pd

from ase.io import read
from ase.neighborlist import mic
from sklearn.cluster import KMeans


def find_poscars(root="."):
    files = []
    for path, dirs, names in os.walk(root):
        for name in names:
            if name.upper() == "POSCAR":
                files.append(os.path.join(path, name))
    return files


def get_nb_feature(poscar):

    atoms = read(poscar)

    nb = [i for i, x in enumerate(atoms.symbols) if x == "Nb"]

    if len(nb) != 3:
        raise ValueError(f"{poscar}: Nb number={len(nb)}")

    pos = atoms.positions[nb]

    dist = []

    for i in range(3):
        for j in range(i + 1, 3):
            vec = pos[j] - pos[i]

            if atoms.pbc.any():
                vec = mic(vec, atoms.cell, atoms.pbc)

            dist.append(np.linalg.norm(vec))

    return np.sort(dist)


def save_feature(poscar, feature):

    folder = os.path.dirname(poscar)

    outfile = os.path.join(folder, "Nb_triangle_feature.dat")

    with open(outfile, "w") as f:
        f.write("Nb_Nb_distance(Angstrom)\n")
        f.write("{:.6f} {:.6f} {:.6f}\n".format(*feature))


def extract_features(poscars):

    data = []

    for p in poscars:
        try:
            feature = get_nb_feature(p)

            save_feature(p, feature)

            data.append([p, feature[0], feature[1], feature[2]])

        except Exception as e:
            print("Skip:", p, e)

    df = pd.DataFrame(data, columns=["POSCAR", "d1", "d2", "d3"])

    return df


def do_cluster(df, n_cluster):

    X = df[["d1", "d2", "d3"]].values

    model = KMeans(n_clusters=n_cluster, random_state=10, n_init=50)

    label = model.fit_predict(X)

    df["cluster"] = label

    return df


def copy_cluster_folder(df):

    output = "cluster_result"

    os.makedirs(output, exist_ok=True)

    for _, row in df.iterrows():
        poscar = row["POSCAR"]
        label = int(row["cluster"])

        cluster_dir = os.path.join(output, f"cluster_{label}")

        os.makedirs(cluster_dir, exist_ok=True)

        src = os.path.dirname(poscar)

        name = os.path.basename(src)

        dst = os.path.join(cluster_dir, name)

        if os.path.exists(dst):
            shutil.rmtree(dst)

        shutil.copytree(src, dst)


def main():

    # 聚类数量
    n_cluster = 10

    poscars = find_poscars(".")

    print(f"Find {len(poscars)} POSCAR")

    df = extract_features(poscars)

    df = do_cluster(df, n_cluster)

    df.to_csv("Nb_triangle_clustering.csv", index=False)

    copy_cluster_folder(df)

    print("Finished")


if __name__ == "__main__":
    main()
