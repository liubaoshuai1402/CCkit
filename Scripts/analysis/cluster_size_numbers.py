import numpy as np
from ase.io import read
from collections import Counter
import argparse

def find_clusters(dist_matrix, cutoff):
    N = dist_matrix.shape[0]
    visited = np.zeros(N, dtype=bool)
    clusters = []
    # clusters: list of connected clusters
    # e.g. [[0,1,3],[2,5],[4]]
    # each sublist contains atom indices belonging to one cluster
    for i in range(N):
        if visited[i]:
            continue
        stack = [i]
        visited[i] = True
        comp = []
        while stack:
            a = stack.pop()
            comp.append(a)
            neigh = np.where(dist_matrix[a] < cutoff)[0]
            for n in neigh:
                if not visited[n]:
                    visited[n] = True
                    stack.append(n)
        clusters.append(comp)
    return clusters

def count_cluster(traj_file,sampling_interval,species,cutoff):
    traj=read(traj_file,index=":")
    frames=traj[::sampling_interval]
    cluster_num=[]
    cluster_sizes=[]
    for frame in frames:
        symbols=np.array(frame.get_chemical_symbols())
        element_idx=np.where(symbols==species)[0]
        if len(element_idx)==0:
            continue

        sub_atoms=frame[element_idx]
        dist=sub_atoms.get_all_distances(mic=True)
        clusters=find_clusters(dist,cutoff)
        cluster_num.append(len(clusters))
        # 收集所有团簇尺寸
        cluster_sizes.extend(len(c) for c in clusters)
    cluster_sizes=np.array(cluster_sizes)
    results={
        "mean_cluster_number":np.mean(cluster_num),
        "mean_cluster_size":np.mean(cluster_sizes),
        "std_cluster_size":np.std(cluster_sizes),
        "max_cluster_size":np.max(cluster_sizes),
        "min_cluster_size":np.min(cluster_sizes),
        "cluster_size_distribution":dict(Counter(cluster_sizes))
    }
    return results

def main():
    parser=argparse.ArgumentParser(
        description="Cluster statistics from MD trajectory"
    )

    parser.add_argument(
        "--input",
        type=str,
        default="dump.xyz",
        help="ASE supported trajectory file"
    )

    parser.add_argument(
        "--sampling_interval",
        type=int,
        default=1,
        help="sampling interval of trajectory"
    )

    parser.add_argument(
        "--species",
        type=str,
        default="H",
        help="Element for cluster analysis"
    )

    parser.add_argument(
        "--cutoff",
        type=float,
        default=2.0,
        help="Cluster cutoff distance (Å)"
    )

    args=parser.parse_args()

    results=count_cluster(
        args.input,
        args.sampling_interval,
        args.species,
        args.cutoff
    )

    with open(f"cluster_statistics_{args.cutoff}.txt","w",encoding="utf-8") as f:
        def log(s=""):
            print(s)
            f.write(s+"\n")

        log("===== Cluster Statistics =====")
        log(f"Species                : {args.species}")
        log(f"Cutoff (Å)             : {args.cutoff:.3f}")
        log(f"Average cluster number : {results['mean_cluster_number']:.3f}")
        log(f"Average cluster size   : {results['mean_cluster_size']:.3f}")
        log(f"Std. cluster size      : {results['std_cluster_size']:.3f}")
        log(f"Largest cluster        : {results['max_cluster_size']}")
        log(f"Smallest cluster       : {results['min_cluster_size']}")

        log()
        log("Cluster size distribution")
        log(" Size    Count")
        for size,count in sorted(results["cluster_size_distribution"].items()):
            log(f"{size:5d} {count:8d}")


if __name__=="__main__":
    main()