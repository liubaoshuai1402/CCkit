# CCkit 功能说明：
# 从多个 VASP OUTCAR 中提取并比较能量与力结果。
import re, argparse
import numpy as np
from ase.io import read


def get_setting(outcar):
    txt = open(outcar, errors="ignore").read()
    encut = re.search(r"ENCUT\s*=\s*([\d.]+)", txt)
    encut = float(encut.group(1)) if encut else None
    kpoint = None
    #从OUTCAR读取NKPTS
    if kpoint is None:
        nk = re.search(r"NKPTS\s*=\s*(\d+)", txt)
        if nk:
            kpoint = f"{nk.group(1)} points"
    return encut, kpoint


def load_outcar(path):

    atoms = read(path, format="vasp-out")
    encut, kpoint = get_setting(path)
    return {
        "E": atoms.get_potential_energy(force_consistent=True),
        "F": atoms.get_forces(),
        "S": atoms.get_stress(),
        "ENCUT": encut,
        "KPOINT": kpoint,
        "length": len(atoms)
    }


def force_error(f1, f2):

    diff = f1 - f2
    atom_rms = np.sqrt(np.mean(diff**2, axis=1))
    return (
        atom_rms.max(),
        atom_rms.sum(),
        np.sqrt(np.mean(diff**2)),
        atom_rms.argmax() + 1,
    )


def compare(out1, out2):

    a = load_outcar(out1)
    b = load_outcar(out2)

    maxF, sumF, rmsF, atom = force_error(a["F"], b["F"])

    print(f"{'Item':<28}{'OUTCAR1':<18}{'OUTCAR2':<18}")
    print("-" * 64)
    print(f"{'ENCUT':<28}{str(a['ENCUT']):<18}{str(b['ENCUT']):<18}")
    print(f"{'KPOINT':<28}{str(a['KPOINT']):<18}{str(b['KPOINT']):<18}")
    print(f"{'Energy difference(meV/atom)':<28}{abs(a['E'] - b['E']) * 1000 / a['length']:.6f}")
    print(f"{'Max atom force RMS(meV/A)':<28}{maxF * 1000:.6f}")
    print(f"{'Sum atom force RMS(meV/A)':<28}{sumF * 1000:.6f}")
    print(f"{'System force RMS(meV/A)':<28}{rmsF * 1000:.6f}")
    print(f"{'Stress difference(meV/atom)':<28}{np.linalg.norm(a['S'] - b['S']) * 1000 / a['length']:.6f}")
    print(f"{'Max error atom index':<28}{atom}")


def main():

    parser = argparse.ArgumentParser(
        description="Compare VASP OUTCAR energy and force errors"
    )

    parser.add_argument("outcar1")

    parser.add_argument("outcar2")

    args = parser.parse_args()

    compare(args.outcar1, args.outcar2)


if __name__ == "__main__":
    main()
