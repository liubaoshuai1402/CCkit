from ase.io import read,write
import os
import argparse
import random


def split(dataset, valid_ratio, test_ratio,seed,shuffle=None):
    random.seed(seed)
    if shuffle:
        random.shuffle(dataset)
    valid_size = int(len(dataset) * valid_ratio)
    test_size = int(len(dataset) * test_ratio)

    valid_set = dataset[:valid_size]
    test_set = dataset[valid_size:valid_size+test_size]
    train_set = dataset[valid_size+test_size:]

    write('train.xyz', train_set)
    write('valid.xyz', valid_set)
    write('test.xyz', test_set)
    print(f"Dataset split into {len(train_set)} training, {len(valid_set)} validation, and {len(test_set)} test structures.")

def main():
    parser = argparse.ArgumentParser(description="Split dataset into train, valid, test sets")

    parser.add_argument("input", type=str, help="Input dataset file")
    parser.add_argument("--valid_ratio", type=float, default=0.05, help="Validation set ratio, default=0.05")
    parser.add_argument("--test_ratio", type=float, default=0.05, help="Test set ratio, default=0.05")
    parser.add_argument("--seed", type=int, default=1214, help="Random seed for shuffling, default=1214")
    parser.add_argument("--shuffle", action='store_true', help="Shuffle dataset before splitting")

    args = parser.parse_args()

    db = read(args.input, ':')
    split(db, args.valid_ratio, args.test_ratio, args.seed, args.shuffle)

if __name__ == "__main__":
    main()