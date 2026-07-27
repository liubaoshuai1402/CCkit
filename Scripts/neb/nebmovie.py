import os
import sys
from ase.io import read,write

def get_images():
    dirs=[d for d in os.listdir(".") if d.isdigit() and os.path.isdir(d)]
    return sorted(dirs,key=lambda x:int(x))

def get_filename(folder,choice):
    if choice=="0":
        files=["POSCAR"]
    elif choice=="1":
        files=["CONTCAR","POSCAR"]
    else:
        raise ValueError("Input must be 0 or 1")

    for f in files:
        path=os.path.join(folder,f)
        if os.path.exists(path):
            return path

    return None

def neb_to_xyz(choice):
    images=[]
    dirs=get_images()

    if not dirs:
        raise RuntimeError("No NEB image directories found")

    for d in dirs:
        path=get_filename(d,choice)

        if path is None:
            print(f"Warning: no POSCAR/CONTCAR in {d}, skip")
            continue

        atoms=read(path)

        if atoms.pbc.any():
            atoms.wrap()

        atoms.info["image"]=int(d)
        images.append(atoms)

        print(f"Read {path}")

    if len(images)==0:
        raise RuntimeError("No structures were loaded")

    write("movie.extxyz",images,format="extxyz")

    print("\nFinished")
    print(f"Total images: {len(images)}")
    print("Output: movie.extxyz")

def main():
    if len(sys.argv)!=2:
        print("Usage:")
        print("  python neb2xyz.py 0   # prefer POSCAR")
        print("  python neb2xyz.py 1   # prefer CONTCAR, fallback POSCAR")
        sys.exit()

    choice=sys.argv[1]

    neb_to_xyz(choice)

if __name__=="__main__":
    main()