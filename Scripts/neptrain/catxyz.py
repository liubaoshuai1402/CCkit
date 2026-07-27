from ase.io import read,write
import argparse


def main():
    parser=argparse.ArgumentParser(description='Merge xyz files using ASE')
    parser.add_argument('files',nargs='+')
    parser.add_argument('-o','--output',default='out.xyz')
    args=parser.parse_args()

    db=[]
    for f in args.files:
        print(f'Reading {f}')
        db.extend(read(f,':'))

    print(f'Total configurations: {len(db)}')
    write(args.output,db,format='extxyz')
    print(f'Saved: {args.output}')


if __name__=='__main__':
    main()