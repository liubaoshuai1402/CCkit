#!/usr/bin/env python3
import imageio.v2 as imageio
import glob
import os
import re
import argparse

def sort_key(x):
    nums=re.findall(r'\d+',os.path.basename(x))
    return int(nums[0]) if nums else 0

def png2mp4(output="animation.mp4",fps=10):
    files=sorted(glob.glob("*.png"),key=sort_key)

    if not files:
        print("No PNG files found.")
        return

    writer=imageio.get_writer(output,fps=fps)

    for f in files:
        print(f"Processing: {f}")
        writer.append_data(imageio.imread(f))

    writer.close()
    print(f"Saved: {output}")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Convert PNG images to MP4")
    parser.add_argument("-o","--output",default="animation.mp4",help="output mp4 filename")
    parser.add_argument("-f","--fps",type=float,default=1.5,help="frames per second")

    args=parser.parse_args()

    png2mp4(args.output,args.fps)