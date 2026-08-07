# CCkit 功能说明：
# 根据 GPUMD 的 NPT 热力学输出计算平均应力。
import numpy as np
import os
import argparse

def average_stress(nptdir):

    thermo_path = os.path.join(nptdir,'thermo.out')
    thermo = np.loadtxt(thermo_path)
    stress_ave = -np.sum(thermo[:,3:9],axis=0)/len(thermo)
    return stress_ave

def main():
    parser = argparse.ArgumentParser(description="get average stress from thermo.out and write to stress.txt")

    parser.add_argument("--nptdir", type=str, default='.',help="the directory run npt, default is .")

    args = parser.parse_args()

    stress_temp = average_stress(args.nptdir)
    np.savetxt(os.path.join(args.nptdir,'stress.txt'),stress_temp)


if __name__ == "__main__":
    main()
