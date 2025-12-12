from ase.io import read
from ase.io.vasp import write_vasp
import os
import shutil
import argparse

def prepare_sp(db,submit,KPOINTS=False):
    cwd = os.getcwd()
    singlepoint_path = os.path.join(cwd,'singlepoint')
    for number,at in enumerate(db):
        
            number_path = os.path.join(singlepoint_path,str(number))
            os.makedirs(number_path)
            
            INCAR_origin_path = os.path.join(cwd,'INCAR') 
            INCAR_path = os.path.join(number_path,'INCAR')
            shutil.copy(INCAR_origin_path,INCAR_path)
        
            POTCAR_origin_path = os.path.join(cwd,'POTCAR')
            POTCAR_path =os.path.join(number_path,'POTCAR')
            shutil.copy(POTCAR_origin_path,POTCAR_path)
            
            if KPOINTS:
                KPOINTS_origin_path = os.path.join(cwd,'KPOINTS')
                KPOINTS_path = os.path.join(number_path,'KPOINTS')
                shutil.copy(KPOINTS_origin_path,KPOINTS_path)
        
            submit_origin_path = os.path.join(cwd,submit)
            submit_path = os.path.join(number_path,submit)
            shutil.copy(submit_origin_path,submit_path)
        
            POSCAR_path = os.path.join(number_path,'POSCAR')
            write_vasp(POSCAR_path,at,direct=True,sort=True)


def main():
    parser = argparse.ArgumentParser(description="Single point calculation generator for vasp.")

    parser.add_argument("input", type=str, help="Input structure file")
    parser.add_argument("--slice",type=str,default=":",help="Set a slice for list [ase atoms]")
    parser.add_argument("--submit",type=str,help="Let this function know the name of your submit file ")
    parser.add_argument("--KPOINTS", action="store_true", help="If set, copy KPOINTS")

    args = parser.parse_args()

    db = read(args.input, args.slice)
    prepare_sp(db, args.submit, args.KPOINTS)

if __name__ == "__main__":
    main()