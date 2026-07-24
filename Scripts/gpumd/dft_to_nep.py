from ase.io import read,write
import os
import argparse

def outcar_to_nepxyz(pos,output):
    db = []
    for root,dirs,files in os.walk(pos):
        if 'OUTCAR' in files:
            outcar_path = os.path.join(root,'OUTCAR')
            db = db + read(outcar_path,':')
    for at in db:
        at.info['energy'] = at.get_potential_energy(force_consistent=True)
        at.info['stress'] = at.get_stress(voigt=True)
        at.arrays['force'] = at.get_forces()
        at.calc = None
    write(output,db)
    print(f"There are {len(db)} OUTCARs, {output} is generated")

def main():
    parser = argparse.ArgumentParser(description="Convert all OUTCAR into one xyz file for NEP")
    parser.add_argument("--pos",type=str,default=".",help="where are your outcars,default = . ")
    parser.add_argument("--output",type=str,default='dataset.xyz',help="File name of output,default = dataset.xyz")

    args = parser.parse_args()

    outcar_to_nepxyz(args.pos, args.output)

if __name__ == "__main__":
    main()