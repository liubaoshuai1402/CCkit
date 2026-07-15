import numpy as np
from ase.io import read
import matplotlib.pyplot as plt
import argparse

def find_clusters(dist_matrix, cutoff):
    N = dist_matrix.shape[0]
    visited = np.zeros(N, dtype=bool)
    clusters = []

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

def fragmentation_scan(traj_file, sampling_interval, species, min_cutoff, max_cutoff, points):

    traj = read(traj_file, index=":")
    frames = traj[::sampling_interval]
    frag = []
    cutoffs = np.linspace(min_cutoff,max_cutoff,points)
    distances = []
    for frame in frames:
        symbols = np.array(frame.get_chemical_symbols())
        element_idx = np.where(symbols == species)[0]
        if len(element_idx) == 0:
            continue
        sub_atoms = frame[element_idx]
        dist = sub_atoms.get_all_distances(mic=True)
        distances.append(dist)
    for cutoff in cutoffs:
        fragmented = []
        for dist in distances:
            clusters = find_clusters(dist,cutoff)
            fragmented.append(1 if len(clusters) > 1 else 0)
        frag.append([cutoff,100*np.mean(fragmented)])

    return np.array(frag)

def main():

    parser = argparse.ArgumentParser(
        description="Cluster connectivity analysis from MD trajectory"
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
        "--min",
        type=float,
        default=1.5,
        help="minimum cutoff radius"
    )

    parser.add_argument(
        "--max",
        type=float,
        default=5.0,
        help="maximum cutoff radius"
    )

    parser.add_argument(
        "--points",
        type=int,
        default=25,
        help="number of cutoff points"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="plot fragmentation curve"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="fragmentation_vs_cutoff.txt",
        help="output file name"
    )

    args = parser.parse_args()

    data = fragmentation_scan(
        args.input,
        args.sampling_interval,
        args.species,
        args.min,
        args.max,
        args.points
    )

    # 无header，两列纯数据
    np.savetxt(
        args.output,
        data,
        fmt="%.6f"
    )

    if args.plot:
        plt.figure(figsize=(6,4))
        plt.plot(data[:,0],data[:,1],marker="o")
        plt.xlabel("Cutoff distance (Å)")
        plt.ylabel("Fragmentation (%)")
        plt.tight_layout()
        plt.savefig("fragmentation_vs_cutoff.png", dpi=300)
        plt.show()

if __name__ == "__main__":
    main()
