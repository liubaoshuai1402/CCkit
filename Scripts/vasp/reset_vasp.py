import os

keep_prefix = ("INCAR","KPOINTS","POSCAR","POTCAR")

def clean_files(path="."):
    for name in os.listdir(path):
        filepath = os.path.join(path,name)

        # 跳过文件夹
        if os.path.isdir(filepath):
            continue

        # 保留指定前缀文件
        if name.startswith(keep_prefix):
            continue

        os.remove(filepath)
        print(f"Removed: {name}")

if __name__ == "__main__":
    clean_files()