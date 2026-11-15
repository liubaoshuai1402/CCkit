# CCkit 功能说明：
# 递归读取 VASP OUTCAR，并合并为可选带 config_type 标签的 NEP 训练 XYZ 数据集。
from ase.io import read,write
import os
import argparse
from typing import Optional

def outcar_to_nepxyz(pos: str, output: str, flag: Optional[str] = None) -> None:
    db = []
    for root,dirs,files in os.walk(pos):
        if 'OUTCAR' in files:
            outcar_path = os.path.join(root,'OUTCAR')
            db = db + read(outcar_path,':')
    for at in db:
        at.info['energy'] = at.get_potential_energy(force_consistent=True)
        at.info['stress'] = at.get_stress(voigt=True)
        at.arrays['force'] = at.get_forces()
        if flag is not None:
            at.info['config_type'] = flag
        at.calc = None
    write(output,db,format='extxyz')
    print(f"There are {len(db)} OUTCARs, {output} is generated")

def main():
    parser = argparse.ArgumentParser(description="Convert all OUTCAR into one xyz file for NEP")
    parser.add_argument("--pos",type=str,default=".",help="where are your outcars,default = . ")
    parser.add_argument("--output",type=str,default='dataset.xyz',help="File name of output,default = dataset.xyz")
    parser.add_argument(
        "--flag", type=str,
        help="Set config_type to this label for every output configuration (optional)",
    )

    args = parser.parse_args()

    outcar_to_nepxyz(args.pos, args.output, args.flag)

if __name__ == "__main__":
    main()
