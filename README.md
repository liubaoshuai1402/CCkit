# CCkit
Tools for modeling and analysis of crystal calculation (DFT and MD). 

## Features

- **Python scripts**: a python-user friendly script. 



## Installation

#### Requirement

In CCkit, different Functions need different modules. If these modules are not in your python environment, CCkit will report errors.

In general, `ase`,`pymatgen`,`matplotlib` are often used. I recommend CCkit user to install them in your python environment.

#### Linux user

---

To install `CCkit`, follow these steps:

1. Clone the repository or download the whole project.

2. Set the `CCkit_PATHS` variable in your `~/.bashrc` file, for example:

   ```
   vi ~/.bashrc
   ```

   add these three lines

   ```
   export CCkit_PATHS=/your_dir_of_CCkit
   export PATH=${CCkit_PATHS}:${PATH}
   source ${CCkit_PATHS}/CCkit_completion.sh
   ```

   > [!IMPORTANT]
   >
   > `/your_dir_of_CCkit` should be an actual directory path! 
   >
   > For example, `/your_dir_of_CCkit` can be `~/CCkit` if your download CCkit project in your home directory.

   then

   ```
   source ~/.bashrc
   ```

3. Add executable permissions to the `CCkit` file:

   ```
   cd ${CCkit_PATHS}; chmod +x CCkit
   ```

#### Windows user

---

To install `CCkit`,

Set the `CCkit_PATHS` variables and add same path into `Path`,

<img src="https://xiaoxiaobuaigugujiao.oss-cn-beijing.aliyuncs.com/img/cckit1.png"/>

## Usage

CCkit supports <u>*menu mode*</u> and <u>*command-line mode*</u>

#### Menu Mode

---

1. Open your terminal

2. Type `CCkit`

   ```
   CCkit
   ```

   

3. Choose a function you need

4. Enter parameters 

#### Command-line Mode

---

CCkit accepts two position parameters: `func` and `extra`. 

In fact, CCkit will wake corresponding python script of `func`, then all `extra` flow to this python script.

In `tools.json`, you can find the corresponding relationships of `func` and script name.

##### Function M1001:

This script (generate_strain.py) is designed to generate rattled strain structures. It can be used to generate trainset for ML potential.

For any function in CCkit, you can quickly check all the inputs which it accepts, like this:

```
CCkit M1001 -h
```

CCkit will give you help information:

```
(dpdata) PS D:\Github_repositories\CCkit> CCkit M1001 -h 

run command: 'D:\miniconda3\envs\dpdata\python.exe' 'D:\Github_repositories\CCkit\Scripts\model\generate_strain.py' -h

usage: generate_strain.py [-h] [--rattle RATTLE] [--iter ITER] [--dmin DMIN] [--seed SEED] [-o OUTPUT] input strain_limt N1 N2 M

Random strain structure generator.

positional arguments:
  input                 Input structure file
  strain_limt           max range of strain, please give one positive float, for example,0.5 will be taken as [-0.5,0.5]
  N1                    Number of uniaxial_strain structures
  N2                    Number of affine_strain structures
  M                     Number of rattled structures for each strain structures

options:
  -h, --help            show this help message and exit
  --rattle RATTLE       rattle amplitude (default 0.02): larger rattle, larger displacements
  --iter ITER           int number of Monte Carlo cycles (default 10): larger iter, larger displacements
  --dmin DMIN           Min interatomic distance allowed: smaller dmin, closer the atoms are allowed to get
  --seed SEED           Random seed
  -o OUTPUT, --output OUTPUT
                        Output file
```

Here, I assume 

1. You have a primitve structure file (it can contain one or more structures), named `prim.xyz`
2. You want a strain limiation in [-0.005,0.005], so `strain_limt` is 0.005
3. For each structure your provided, you want to generate 10 uniaxial_strain structures and 10 affine_strain structures, so `N1` and `N2` are both 10
4. For ==each strain structure==, you want to generate 2 rattled strain structures, so `M` is 2.
5. For details about rattling, you choose default vaules.
6. For the name of output file, you choose default vaule. 

Now, you can use this function easily by:

```
CCkit M1001 prim.xyz 0.005 10 10 2
```

In this example, `func` is `M1001` and `extra` is `prim.xyz 0.005 10 10 2`

Finally, `M1001` will generate how many structures ? 

Answer: (the numbers of primitive structure) * (10+10) * 2

> [!IMPORTANT]
>
> Of cause, you should carefully choose suitable rattle details for your own system!!!

The prototype of this code is here: [Structure generation and NEP training](https://calorine.materialsmodeling.org/get_started/generate_training_structures_and_training.html)

##### Function M1002

This script (generate_YSZ.py) can substitute element A by element B and generate vacancies simultaneously. (YSZ is a classical example)

```
(dpdata) PS D:\Github_repositories\CCkit> CCkit M1002 -h

run command: 'D:\miniconda3\envs\dpdata\python.exe' 'D:\Github_repositories\CCkit\Scripts\model\generate_YSZ.py' -h

usage: generate_YSZ.py [-h] [--N2 N2] [--seed SEED] [-o OUTPUT] input elementA elementB N1 elementC M

Random YSZ type generator (conatin substitute and vacancy simultaneously).

positional arguments:


positional arguments:
  input                 Input structure file
  input                 Input structure file
  elementA              Element to replace
  elementB              Element replacing
  N1                    Number of A atoms replaced by B
  elementC              Element to delete
  M                     Number of structures for each prim to generate

options:
  -h, --help            show this help message and exit
  --N2 N2               Number of vacancy of C atoms
  --seed SEED           Random seed, default: 1214
  -o OUTPUT, --output OUTPUT
                        Output file, default: ysztype.xyz
```

Example1:

I assume :

1. You have a POSCAR file (it can also be xyz file and contain more than one structures as you like)
2. Your want to substitute 10 Zr by Y 
3. Your want generate 10/2 O vacancies. (This script always defaults the number of vacancies to half of the number of substitutions)
4. You want only one substitue structure.

```
CCkit M1002 POSCAR Zr Y 10 O 1
```

Example2:

I assume:

1. You have a primitive ZrO2.xyz (it contains 8 structures)
2. Your want to substitute 9 Zr by Y 
3. Your want generate 4 O vacancies.
4. For each primitive structure, you want to generate 3 substitute structures

```
CCkit M1002 ZrO2.xyz Zr Y 9 O 3 --N2 4 
```

Finally, `M1002` generate 8 * 3 = 24 structures.

##### Function M1003 and M1004

This two scripts are very similar to M1002, see help information by:

```
CCkit M1003 -h
CCkit M1004 -h
```

##### Function M1005

This script (generate_sp.py) will convert a trajectory (It can be OUTCAR of AIMD, dump.xyz of GPUMD and other formats) into a series of single-point energy calculation folders. Useful for active learning.

Example1:

I assume:

1. You have filtered this trajectory (1.xyz) and all structures are expected to calculate.
2. Your have INCAR, POTCAR in current directory.
3. You use KSPACING in INCAR while not a KPOINTS file.
4. Your submit file is vasp.pbs (it can also be a slurm script)

```
CCkit M1005 1.xyz --submit vasp.pbs
```

Example2:

If you want to sample one structure every 100 structures and neglect the first 500 structures and use KPOINTS (you should provide KPOINTS in current directory)

```
CCkit M1005 1.xyz --slice 500::100 --submit vasp.pbs --KPOINTS
```

