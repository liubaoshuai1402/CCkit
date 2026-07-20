import os
import sys
from ase.io import read,write


def get_images():
    dirs=[d for d in os.listdir(".") 
          if d.isdigit() and os.path.isdir(d)]
    return sorted(dirs,key=lambda x:int(x))


def neb_to_xyz(filename):

    images=[]

    dirs=get_images()

    if not dirs:
        raise RuntimeError("No NEB image directories found")

    for d in dirs:
        path=os.path.join(d,filename)

        if not os.path.exists(path):
            print(f"Warning: {path} not found, skip")
            continue

        atoms=read(path)

        if atoms.pbc.any():
            atoms.wrap()

        atoms.info["image"]=int(d)

        images.append(atoms)

        print(f"Read {path}")

    if len(images)==0:
        raise RuntimeError("No structures were loaded")

    write(
        "movie.extxyz",
        images,
        format="extxyz"
    )

    print("\nFinished")
    print(f"Total images: {len(images)}")
    print("Output: movie.extxyz")


def main():

    if len(sys.argv)!=2:
        print("Usage:")
        print("  python neb2xyz.py 0   # use POSCAR")
        print("  python neb2xyz.py 1   # use CONTCAR")
        sys.exit()

    choice=sys.argv[1]

    if choice=="0":
        filename="POSCAR"
    elif choice=="1":
        filename="CONTCAR"
    else:
        raise ValueError("Input must be 0 or 1")

    print(f"\nUsing {filename} to generate movie\n")

    neb_to_xyz(filename)


if __name__=="__main__":
    main()