<!-- Begin section: Overview -->

# CCkit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/liubaoshuai1402/cckit)

A command-line toolkit for modeling, preparing, and analyzing crystal-structure calculations. CCkit connects common tasks in DFT, molecular dynamics, NEP machine-learning potentials, and NEB workflows through small Python utilities.

## What CCkit provides

- **Structure modeling**: supercells, strain and rattling, substitutions, vacancies, and structural edits.
- **VASP workflow preparation**: single-point calculation folders, POSCAR cleanup and sorting, surface constraints, and OUTCAR comparison.
- **NEP and GPUMD utilities**: dataset conversion, merging and splitting, configuration labels, NEP relaxation, and NPT averaging.
- **Trajectory and structure analysis**: hydrogen states, hydrogen vacancies, oxygen vacancies, bond distributions, atom displacements, and cluster connectivity.
- **NEB workflow support**: image generation, image alignment, trajectory/movie generation, and DFT-versus-NEP barrier plots.

## Project layout

| Directory | Purpose |
| --- | --- |
| Scripts/model | Build and modify crystal structures |
| Scripts/vasp | Prepare and inspect VASP calculations |
| Scripts/gpumd | GPUMD and NEP utilities |
| Scripts/neptrain | NEP dataset preparation and comparison plots |
| Scripts/neb | NEB image and visualization tools |
| Scripts/analysis | Structural and trajectory analysis |

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

Enable function-name completion in PowerShell (the equivalent of `source CCkit_completion.sh` on Linux):

```powershell
. "D:\your_dir_of_CCkit\CCkit_completion.ps1"
```

To make it take effect automatically in every new PowerShell session, add that line to your `$PROFILE`:

```powershell
Add-Content -Path $PROFILE -Value '. "D:\your_dir_of_CCkit\CCkit_completion.ps1"'
```

If loading the script is blocked by the execution policy, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

After that, type `cckit fix-` and press Tab to complete function names (works in PowerShell 7 and Windows PowerShell 5.1).

## Usage

CCkit supports current menu mode and command-line mode.

### Current command-line usage

List all registered functions:

```powershell
CCkit --listall
```

The current function names and their script mappings are defined in tools.json. The launcher finds the mapped script under CCkit_PATHS and forwards the remaining arguments to it.

Use the function-specific help message before running a task:

```powershell
CCkit generate-strain -h
CCkit dft-to-nep -h
```

General command-line form:

```powershell
CCkit <function> <arguments>
```

### Main workflow areas

- **Structure modeling**: generate supercells, strain/rattled structures, substitutions, vacancies, and edited structures.
- **VASP preparation**: create single-point calculation folders, sort POSCAR files, fix surface atoms, clean calculation directories, and compare OUTCAR results.
- **NEP/GPUMD**: collect DFT data, merge and split datasets, add Config_type labels, relax structures with NEP, and average NPT properties.
- **EOS**: create VASP volume-scan jobs and fit Birch-Murnaghan energy-volume curves.
- **Analysis**: study hydrogen states, hydrogen vacancies, oxygen vacancies, bond distributions, atom displacements, and cluster connectivity.
- **Segregation concentration**: fit paired segregation enthalpy/entropy data with the Cho model and integrate the McLean isotherm.
- **NEB**: generate and align images, make movies, and compare DFT and NEP energy barriers.

### Example workflows

Generate strained and rattled structures:

```powershell
CCkit generate-strain prim.xyz 0.005 10 10 2 -o strained.xyz
```

Prepare VASP single-point calculations from a trajectory:

```powershell
CCkit convert-xyz-sp trajectory.xyz --submit vasp.pbs
```

Build an NEP dataset from VASP calculations:

```powershell
CCkit dft-to-nep --pos ./vasp_calculations
CCkit split-dataset dataset.xyz --valid_ratio 0.1 --test_ratio 0.1 --shuffle
```

Generate NEB images between two structures:

```powershell
CCkit make-neb POSCAR_initial POSCAR_final -n 5
```

Create 11 isotropically scaled VASP jobs from an optimized `CONTCAR`.
By default, `INCAR-2` and `POTCAR` are read beside the structure, and the
`V_970` through `V_1020` folders are created beside it. Once calculations
finish, fit their `OUTCAR` files and write the data, fit parameters, fit curve,
and `EOS.png` into the calculation root:

```powershell
CCkit eos-maker make CONTCAR
CCkit eos-maker fit .
```

Set the volume-ratio range and number of structures with `--start`, `--stop`,
and `--points`. Use `--incar` and `--potcar` for alternate VASP input paths;
existing `V_*` folders are preserved unless `--overwrite` is specified.

Inspect the final cell stress after a VASP relaxation (Python standard library only):

```powershell
CCkit check-stress
CCkit check-stress path/to/OUTCAR
CCkit check-stress path/to/calculation --threshold 0.1
```

The default input is `OUTCAR`; a directory or `OUTCAR.gz` is also accepted.
The command prints the last stress block to the terminal: six components
(`xx yy zz xy yz zx`), the Cartesian tensor, mean normal pressure, maximum
absolute stress/shear/deviatoric component, printed external pressure and
Pulay correction when present, and structural-accuracy/termination markers.
All stress and pressure values, including `--threshold`, use **GPa**
(OUTCAR kbar values are multiplied by 0.1). VASP's sign convention is retained:
positive normal stress indicates compression. See the official
[ISIF documentation](https://vasp.at/wiki/ISIF) and
[PSTRESS documentation](https://vasp.at/wiki/PSTRESS).

`--threshold` is optional, with no default or universal convergence cutoff.
It screens the maximum absolute component against zero only for `ISIF=3/6`
with an explicit zero `PSTRESS` in OUTCAR. Printed values are used without
subtracting `PSTRESS` again. For fixed cells, constrained cell relaxations, or
nonzero `PSTRESS`, interpret the reported stresses according to the calculation
settings. With `ISIF=1`, only the printed external pressure is reported as
reliable. A small stress does not by itself establish ionic or electronic
convergence; an incomplete or malformed final stress block is rejected.

Calculate the average grain-boundary concentration from a two-column file
(enthalpy first, entropy second). The enthalpy and `T*entropy` values must use
the unit selected by `--energy-unit`:

```powershell
CCkit seg-cal enthalpy_entropy.csv 0.01 --temperature 1000 --energy-unit eV
```

The default JSON result is written next to the input file. Use `-o` to choose
another path. The command fits a skew-normal enthalpy marginal by maximum
likelihood, derives the Gaussian entropy marginal from the fitted linear
enthalpy-entropy relation, estimates the Gaussian-copula Pearson parameter
from the paired ranks, and performs deterministic quadrature of the McLean
concentration. `kJ/mol` is also accepted as an energy unit.

CCkit primarily handles POSCAR, XYZ, extended XYZ, and VASP OUTCAR files through ASE and pymatgen. Different functions may additionally require numpy, scipy, matplotlib, hiphive, calorine, imageio, or other workflow-specific packages.

## VASP module: command reference

The commands below map to every script in `Scripts/vasp/`. Run `CCkit <command> -h` for the current argument list. Structure-reading commands use ASE; `compare-vasp-ef` and `vasp-displacement` also use NumPy. `reset-vasp` (also available as `rest-vasp`), `prepare-vasp-batch`, `check-convergence`, and `check-stress` use only the Python standard library.

### `convert-xyz-sp` — trajectory to single-point jobs

Use this to split selected frames of a trajectory with cell information into separate VASP `POSCAR` files. The command first checks for `INCAR` **beside the input trajectory**. If it is absent, no other VASP input is checked or copied, and `--submit` is unnecessary. If `INCAR` is present, the command requires `POTCAR` and a submission script supplied with `--submit` in the same directory. Add `--KPOINTS` to copy a `KPOINTS` file; otherwise the calculation can use `KSPACING` in `INCAR`.

```powershell
CCkit convert-xyz-sp trajectory.xyz
CCkit convert-xyz-sp trajectory.xyz --submit vasp.pbs
CCkit convert-xyz-sp trajectory.xyz --slice 500::100 --submit vasp.pbs --KPOINTS
```

The last example starts at frame 500 and takes every 100th frame. ASE slice syntax is used. The script creates `singlepoint/0`, `singlepoint/1`, and so on **beside the input trajectory**, each with a sorted `POSCAR`. VASP input files are copied only when `INCAR` is present. Missing required files are reported before any output directory is created. Existing numbered directories cause an error; choose an input directory without conflicting `singlepoint` entries before running it.

### `prepare-vasp-batch` — distribute inputs to existing POSCAR directories

Use this after structures have already been placed in separate subdirectories.

The root must contain `INCAR` and `POTCAR`; `KPOINTS` and the job script are optional.

```powershell
CCkit prepare-vasp-batch --root ./calculations --job vasp.pbs
```

The command recursively finds `POSCAR` files **below** the root, then copies the available inputs from the root into each containing directory. It does not process a `POSCAR` in the root itself. The default root is the current directory and the default job script name is `job.slurm`. Existing copies of the input files in target directories are replaced; the `POSCAR` files are left in place.

### `fix-surface` — constrain a fractional-z interval

Fix atoms whose fractional z coordinate falls in `[ZMIN, ZMAX)`; atoms outside that interval remain free. For example, this fixes the lower part of a slab:

```powershell
CCkit fix-surface POSCAR --zrange 0.0 0.3
```

The default output is `POSCAR_fixed` beside the input. Use `-o` to choose another output path. The written VASP structure uses selective-dynamics flags and retains the input atom order.

### `fix-interface` — keep the middle region movable

Fix atoms with fractional z < Z1 or z >= Z2; atoms in `[Z1, Z2)` remain free. This is useful when two outer interface regions should be constrained:

```powershell
CCkit fix-interface POSCAR --z1 0.2 --z2 0.8
```

The bounds must satisfy `0 <= Z1 < Z2 <= 1`. The default output is `POSCAR_fixed` beside the input. A bare filename passed with `-o` is also written beside the input; a path with a directory is used as supplied. The output uses selective-dynamics flags and retains atom order.

### `sort-poscar` — order atoms by element

Specify the desired element order after `-s`:

```powershell
CCkit sort-poscar POSCAR -s Zr Y O -o POSCAR_sorted
```

Elements not listed after `-s` follow the listed elements, retaining their relative order. The output is a VASP structure. If `-o` is omitted, `POSCAR_sorted` is written in the **current working directory**; an explicit output path is used as supplied. Check the reordered atom indices before comparing this file with a structure that uses the original order.

### `vasp-displacement` — inspect relaxation displacements

Compare corresponding atoms in the initial `POSCAR` and relaxed `CONTCAR`:

```powershell
CCkit vasp-displacement
CCkit vasp-displacement ./run/POSCAR ./run/CONTCAR --top 5
```

The defaults are `POSCAR` and `CONTCAR` in the current directory. The terminal report shows the sum of atomic displacement magnitudes and the largest individual displacements in Å, with **zero-based** atom indices. `--top N` controls how many atoms appear in the ranked list: `--top 5` shows the five largest displacements, while the default is 10. If `N` exceeds the atom count, all atoms are shown. This option does not change the total displacement calculation and must be a positive integer. Distances use minimum-image vectors in the initial cell. Both files must have the same atom count and element order. No file is written.

### `compare-vasp-ef` — compare two OUTCAR results

Use two calculations of the same atom-ordered structure, for example to inspect an energy cutoff or k-point change:

```powershell
CCkit compare-vasp-ef ./test-a/OUTCAR ./test-b/OUTCAR
```

The terminal table shows `ENCUT`, `NKPTS`, absolute energy difference per atom, force-difference summaries, an atom index with the largest force RMS difference, and a stress-difference value. The script reads the final structure from each `OUTCAR` with ASE. Its force index is **one-based**. The stress row is computed as `1000 * ||stress_a - stress_b|| / number_of_atoms` from ASE stress values; its printed `meV/atom` label should not be interpreted as a physical stress unit. No file is written.

### `check-convergence` — scan OUTCAR files

Check calculation directories recursively:

```powershell
CCkit check-convergence --root ./calculations
CCkit check-convergence --root ./calculations --no-recursive
```

The default root is the current directory. With `--no-recursive`, only immediate subdirectories are checked; the root's own `OUTCAR` is not included. The terminal report lists each absolute `OUTCAR` path and counts files containing VASP's `reached required accuracy - stopping structural energy minimisation` marker. This checks that marker only; it does not independently verify electronic convergence or normal termination. No file is written.

### `check-stress` — report final cell stress

Inspect the last stress block in an `OUTCAR`, or pass a calculation directory. A file named `OUTCAR.gz` can be passed directly:

```powershell
CCkit check-stress
CCkit check-stress ./run/OUTCAR.gz
CCkit check-stress ./run --threshold 0.1
```

The default input is `OUTCAR` in the current directory. The terminal report gives the six tensor components, Cartesian tensor, pressure, shear and deviatoric summaries, and available convergence and termination markers. Values and `--threshold` use **GPa**; VASP's compression-positive sign convention is retained. The optional threshold screens the maximum absolute tensor component only when the OUTCAR explicitly has `ISIF=3` or `6` and zero `PSTRESS`. It is not a general convergence verdict. For `ISIF=1`, only the printed external pressure is treated as reliable. No file is written.

### `reset-vasp` / `rest-vasp` — preview and confirm directory cleanup

Run this **inside the directory to clean**. Both command names invoke the same tool:

```powershell
CCkit reset-vasp -h
CCkit rest-vasp -h
CCkit rest-vasp 0
CCkit reset-vasp 0 -remain CONTCAR vasp.pbs
```

With no arguments or with `-h` / `--help`, the command only displays help. Cleanup requires the explicit positional mode `0`. It prints the absolute directory and the complete list of files to delete, then asks `y/n`. Only `y` (case-insensitive, allowing surrounding whitespace) proceeds. `n`, an empty response, any other response, end of input, or Ctrl+C at the prompt cancels without deleting files. If there are no candidates, it reports that and exits.

The default keep rule preserves names starting with `INCAR`, `KPOINTS`, `POSCAR`, or `POTCAR`, including backup variants. Directories and their contents are skipped; cleanup does not recurse. Other files, including `OUTCAR`, `CONTCAR`, and submission scripts, are deletion candidates unless explicitly kept.

Use `-remain FILE [FILE ...]` (or `--remain`) to preserve additional **exact filenames** alongside the default prefixes. Multiple names and repeated options are supported; quote names containing spaces. Names are matched case-sensitively, and paths and wildcard patterns are not supported. Missing names or directory names cause an error before cleanup so a misspelled keep name cannot silently proceed. For example, the last command above also keeps `CONTCAR` and `vasp.pbs`.

Only files in the displayed list are deleted after confirmation; newly created files are not added. Deletion is permanent. A deletion error stops cleanup and reports the affected path; files already reported as removed remain deleted. **Migration:** existing calls to bare `CCkit reset-vasp` must now use `CCkit reset-vasp 0` and supply an interactive `y` confirmation.

## Model module: command reference

These are the 11 public commands backed by `Scripts/model/`. Atom indices in the examples are **zero-based**. Several older commands still write their default output to the current working directory; the location for each command is stated below. Use `CCkit <command> -h` to inspect all options.

### `generate-strain` — strained and rattled training structures

For every frame in an ASE-readable input, generate `N1` random uniaxial strains and `N2` random affine strains, then make `M` Monte Carlo rattled structures from each strained structure:

```powershell
CCkit generate-strain prim.xyz 0.005 10 10 2 --seed 1214
```

Here the strain components are sampled within `[-0.005, 0.005]`, and each input frame produces `(10 + 10) * 2 = 40` output frames. `--rattle`, `--iter`, and `--dmin` control the perturbation; the default output is `rattled_strain_structures.xyz` in the current working directory, or the path supplied with `-o`. This command requires ASE, NumPy, and hiphive.

### `generate-ysz` — substitution and vacancies together

Randomly replace `N1` atoms of element A with B and delete `N2` atoms of element C in every input frame. The final positional argument `M` is the number of variants per frame:

```powershell
CCkit generate-ysz POSCAR Zr Y 10 O 3 --seed 1214
```

If `--N2` is omitted, `N2` is `N1 // 2` (five O vacancies in this example); use `--N2 4` to override it. The default output is `ysztype.xyz` in the current working directory. Supply a structure with enough A and C atoms for each requested variant.

### `generate-vacancy` — random vacancies

Delete `N` randomly selected atoms of one element and generate `M` variants from a **single** input structure:

```powershell
CCkit generate-vacancy POSCAR O 2 5 --seed 1214
```

The default output is `vacancy_structures.xyz` in the current working directory; `-o` sets another file. The command fails if fewer than `N` atoms of the selected element are present.

### `generate-substitute` — random substitutions

Replace `N` randomly selected atoms of element A with B and generate `M` variants from a **single** input structure:

```powershell
CCkit generate-substitute POSCAR Zr Y 2 5 --seed 1214
```

The default output is `substituted.xyz` in the current working directory; `-o` sets another file. The command fails if fewer than `N` atoms of A are present. For substitution **plus** vacancies in each variant, use `generate-ysz`.

### `generate-sol` — enumerate ordered doping arrangements

Use pymatgen and enumlib to enumerate symmetry-distinct arrangements after replacing a specified number of host atoms with a dopant:

```powershell
CCkit generate-sol POSCAR Y 2 --host Zr --max_structures 100
```

`--host` defaults to `Zr`; `--max_structures` defaults to 10000. The command uses a one-cell enumeration and writes numbered `POSCAR` files inside `<dopant><number>_structures/` in the current working directory (for this example, `Y2_structures/`). It requires pymatgen and an available enumlib installation.

### `supercell` — repeat a crystal cell

Repeat one input structure by integer factors along its three cell vectors:

```powershell
CCkit supercell POSCAR 2 2 2 --output supercell.xyz
```

The output defaults to `supercell.xyz` in the current working directory. This command reads one structure, so provide a single-frame input.

### `add-atom` — place one atom by position or geometry

Choose one of three modes. `position` uses Cartesian coordinates, `center` uses the midpoint of two indexed atoms, and `OH` places an atom beyond O along the M-to-O direction:

```powershell
CCkit add-atom POSCAR --mode position --position 1.0 2.0 3.0 --element H
CCkit add-atom POSCAR --mode center --atomA 0 --atomB 1
CCkit add-atom POSCAR --mode OH --M 0 --O 1 --distance 1.0
```

The added element defaults to H; `--distance` defaults to 1.0 Å. By default, the script writes beside the input with a name beginning `POSCAR_` and ending in the chosen coordinates or atom indices. `--output` changes that **base name**, and the mode-specific suffix is still appended; a relative base name is resolved from the current working directory.

### `remove-atom` — remove indexed atoms

Remove one or more atoms by index, optionally sorting the remaining elements with `-s`:

```powershell
CCkit remove-atom POSCAR 0 3 -s Zr O
```

The default file is `POSCAR_removed_0_3` beside the input. `-o` changes the output **base name**; the removed indices are appended. Indices outside the input atom range are rejected.

### `substitute-atom` — replace indexed atoms

Replace one or more indexed atoms with the element supplied to `-e`; `-s` optionally sorts the result by element:

```powershell
CCkit substitute-atom POSCAR 3 5 -e Y -s Zr Y O
```

The default file is `POSCAR_replaced_Y_3_5` beside the input. `-o` changes the output **base name**; the new element and indices are appended. Indices outside the input atom range are rejected. Unlike `generate-substitute`, this command changes the atoms you name rather than sampling them randomly.

### `move-crystal` — move a selected atom to the origin

Translate the whole structure by the negative Cartesian position of one atom, then wrap atoms into the periodic cell:

```powershell
CCkit move-crystal POSCAR 0 --output POSCAR_shifted
```

Without `--output`, the script writes `POSCAR_shifted_atom0` in the current working directory. The relative arrangement of atoms is preserved by the translation.

### `line-dimer` — add two atoms on a line

Take the midpoint of two indexed atoms and append two atoms at `+r` and `-r` along their connecting line:

```powershell
CCkit line-dimer POSCAR 0 1 --type_dimer H --r 0.37
```

The default element is H, and `r` defaults to 0.37 Å, giving a separation of `2r` between the added atoms. The output defaults to `dimer_added.xyz` in the current working directory; `--output` sets another file. Choose two atoms at different positions so the line has a defined direction.

## GPUMD module: command reference

All six scripts in `Scripts/gpumd/` are registered as public commands. Depending on the command, ASE and/or NumPy are required; `relax-nep` additionally requires calorine and a trained NEP potential.

### `dft-to-nep` — collect VASP results into an XYZ dataset

Recursively find `OUTCAR` files under a calculation directory and read **all frames** from each one:

```powershell
CCkit dft-to-nep --pos ./vasp_calculations --output dataset.xyz
```

The script stores each frame's force-consistent energy, stress, and atomic forces in an extended XYZ dataset for NEP training. `--pos` defaults to the current directory; `--output` defaults to `dataset.xyz` in the current working directory. The printed count is the number of collected frames, even though the message calls them OUTCARs. Check the generated dataset before using it for training.

### `split-dataset` — make train, validation, and test sets

Split every frame of an ASE-readable dataset into three XYZ files:

```powershell
CCkit split-dataset dataset.xyz --valid_ratio 0.1 --test_ratio 0.1 --shuffle --seed 1214
```

The validation and test ratios each default to `0.05`; their set sizes are truncated to integers, and the remaining frames go to training. `--shuffle` randomizes frames before splitting; without it, frames keep their input order and `--seed` has no effect. The outputs are always `train.xyz`, `valid.xyz`, and `test.xyz` in the **current working directory**, replacing files with those names. Use a dataset large enough to populate the requested sets.

### `relax-nep` — optimize a structure with an NEP potential

Use calorine's CPU NEP calculator to relax one structure:

```powershell
CCkit relax-nep -i POSCAR --nep nep.txt --isif 3 --steps 200 --fmax 0.01
```

The defaults are `POSCAR`, `nep.txt`, the `fire` minimizer, 200 steps, and `fmax=0.01` eV/Å. `--isif 3` relaxes the atoms and cell; `--isif 2` keeps the cell fixed. Only these two values trigger optimization in the current script. By default it writes `relaxed.xyz`, `energy.txt`, `POSCAR_relaxed`, and `log.out` in the current working directory. `--out` and `--energy` can select other paths for the first two files; `POSCAR_relaxed` and `log.out` keep their fixed names and locations.

### `average-cell` — average an NPT cell

Read `model.xyz` and `thermo.out` from one GPUMD NPT directory:

```powershell
CCkit average-cell --nptdir ./npt_run
```

The script averages all rows of the nine cell-vector columns in `thermo.out` (zero-based columns 9–17), then scales the atoms of `model.xyz` into the mean cell. It writes `model_temp.xyz` in the same NPT directory. `--nptdir` defaults to the current directory; there is no burn-in or time-window option.

### `average-stress` — average NPT stress components

Read `thermo.out` from one GPUMD NPT directory:

```powershell
CCkit average-stress --nptdir ./npt_run
```

The script averages all rows of the six stress columns (zero-based columns 3–8), reverses their signs, and writes the six resulting values to `stress.txt` in the NPT directory. `--nptdir` defaults to the current directory. Values retain the units of `thermo.out`; no unit conversion or burn-in selection is performed.

### `group-type` — label XYZ atoms by element

Add a per-atom integer `group` array to every `.xyz` or `.extxyz` file directly inside a folder:

```powershell
CCkit group-type ./xyz
CCkit group-type ./xyz --order O Zr H Y
```

Each input frame is preserved in a new extended XYZ file beside its source, named `<input>_group.xyz` (or `<input>_group.extxyz`). The same element-to-ID mapping is used across the whole folder. By default, elements present from `H O Zr Y` receive IDs first in that order, followed by any other elements alphabetically; `--order` changes the preferred order. Only elements present receive IDs, so they are contiguous from zero. The command prints the mapping, skips files already ending in `_group`, and leaves source files unchanged. It refuses to replace existing outputs unless `--overwrite` is supplied. It does not search subdirectories.

## Analysis module: command reference

Eight scripts in `Scripts/analysis/` are registered as public commands. They analyze structures, trajectories, bond lengths, vacancies, clusters, or segregation data. Bond, hydrogen, and vacancy analyses need structures with cell information, such as POSCAR or extended XYZ with lattice metadata. The older analysis commands generally write results in the **current working directory**; check each entry before running them from another directory. Use `CCkit <command> -h` for the full argument list.

### `global-bond` — bond lengths across a trajectory

Collect distances from each atom of element A to neighboring atoms of element B within a cutoff, across **all frames** of an ASE-readable input:

```powershell
CCkit global-bond trajectory.extxyz O Zr 2.8
CCkit global-bond trajectory.extxyz O Zr 2.8 --plt
```

The command writes `bands_dis_global.txt` with all selected distances, `shortbands_dis_global.txt` for distances from 1.80 to 2.20 Å, and `longbands_dis_global.txt` for distances above 2.20 through 2.60 Å. These short/long ranges are fixed in the script and do not change with the cutoff. All files are written in the current working directory. `--plt` additionally writes three `*_KDE_global.txt` files and three `*bonds_dis_global.png` plots; KDE needs enough nonidentical distances in each category.

### `local-bond` — bond lengths near hydrogen

For each H atom, find nearby A atoms within `cutoff1`, then measure their A–B bonds within `cutoff2`:

```powershell
CCkit local-bond trajectory.extxyz O Zr 1.2 2.8
```

It writes `bands_dis_local.txt`, `shortbands_dis_local.txt`, and `longbands_dis_local.txt` in the current working directory; `--plt` adds KDE text files and PNG plots. The fixed short/long ranges are the same as for `global-bond`. **For a trajectory, the current implementation resets its distance lists for each frame and writes only the final frame's results.** Use a single-frame input when earlier frames must not be discarded.

### `hydrogen-state` — classify hydrogen in each frame

Count H bonded to O, isolated interstitial H, and other H with nearby atoms:

```powershell
CCkit hydrogen-state trajectory.extxyz --OHdist 1.2 --r 2.0
```

An H is bonded if an O lies within `--OHdist` Å. Otherwise it is interstitial if **no atom** lies within `--r` Å, and transitive if at least one neighbor does. The command writes per-frame counts to `count_H_state.txt` and their averages to `count_H_state_avg.txt`, both in the current working directory. The values shown are the defaults for the two radii.

### `hydrogen-vacancy` — count isolated hydrogen

Despite the command name, this script counts H atoms with **no neighboring atom** within a radius; it does not locate vacant H sites:

```powershell
CCkit hydrogen-vacancy trajectory.extxyz --r 1.8
```

The radius defaults to 1.8 Å. It writes one interstitial-H count per frame to `count_H_vacancy.txt` and the mean count to `count_H_vacancy_avg.txt` in the current working directory.

### `cluster-connect` — scan fragmentation against distance

For a selected element, connect atoms whose minimum-image separation is **less than** each tested cutoff. A sampled frame is fragmented when it has more than one cluster:

```powershell
CCkit cluster-connect --input dump.xyz --species H --min 1.5 --max 5.0 --points 25 --sampling_interval 10 --plot
```

The two-column output gives cutoff in Å and the percentage of sampled frames that are fragmented. It defaults to `fragmentation_vs_cutoff.txt` in the current working directory; `--output` selects another path. `--plot` also saves `fragmentation_vs_cutoff.png` in the current working directory and opens the plot. Frames without the selected element are skipped. The default input is `dump.xyz`, species is H, and every frame is sampled unless `--sampling_interval` is set.

### `cluster-size` — summarize cluster sizes

Use one cutoff to count connected clusters of a selected element in sampled frames:

```powershell
CCkit cluster-size --input dump.xyz --species H --cutoff 2.0 --sampling_interval 10
```

The command prints and saves the mean number of clusters per analyzed frame, mean/standard deviation/minimum/maximum cluster size, and a size-count distribution pooled across frames. Its file is `cluster_statistics_<cutoff>.txt` in the current working directory, using the supplied floating-point cutoff in the name. Defaults are `dump.xyz`, H, 2.0 Å, and every frame. Frames without the selected element are skipped; distances use minimum-image convention and pairs connect only below the cutoff.

### `find-vacancy` — locate missing element sites

Compare a defect-free reference with a defective structure or trajectory. Oxygen is the default element:

```powershell
CCkit find-vacancy reference.extxyz defective.extxyz
CCkit find-vacancy reference.extxyz defective.extxyz --method ws --tolerance 1.2
```

The default `density` method maps the reference element positions into each defective cell, finds peaks in the difference of periodic Gaussian densities, and reports candidate positions in that cell. `--number` sets how many peaks to keep; without it, the script uses at least one and otherwise the reference-minus-current element count. `--spacing`, `--sigma`, and `--minimum-distance` control the density search. `--method ws` instead matches reference sites one-to-one within `--tolerance` Å; unmatched sites are vacancies. `--cores` processes independent frames in parallel.

By default, the script writes marked frames to `oxygen_vacancies.extxyz` and coordinates to `oxygen_vacancies.csv` in the **current working directory**, even if another element is selected. Use `-o` and `--report` to set different paths. Dummy `X` atoms mark candidate sites in the trajectory; `--marker none` omits them. The CSV includes frame number, fractional and Cartesian coordinates, method, and assignment distance (available for `ws`; `NaN` for `density`).

### `seg-cal` — average grain-boundary segregation concentration

Read paired segregation enthalpy and entropy values from two columns of a text or CSV file:

```powershell
CCkit seg-cal enthalpy_entropy.csv 0.01 --temperature 1000 --energy-unit eV
```

The second argument is bulk solute concentration, strictly between 0 and 1. The command fits a skew-normal enthalpy distribution, derives entropy statistics from a linear fit, estimates a Gaussian copula from paired ranks, and integrates the McLean isotherm. `--temperature` is required in K. Enthalpy and `temperature × entropy` must use the chosen energy unit (`eV` by default, or `kJ/mol`); `--quadrature-order` defaults to 60. It prints the average concentration and writes fitted parameters and the result to `<input-stem>_segregation.json` beside the input. A bare `-o` filename is also placed beside the input.

### `atom_displacement.py` — unfinished helper

This file is **not registered as a CCkit command**. It defines a function intended to compute Cartesian displacement magnitudes between corresponding atoms in two structures, requiring equal atom counts, but has no command-line entry point or output handling. It also references NumPy without importing it, so the function cannot currently be used as written.

## NEB module: command reference

All four scripts in `Scripts/neb/` are public commands. `align-neb` and `make-neb` prepare VASP structures; `neb-movie` collects image structures; `png-to-mp4` makes a video from PNG files. The commands write to the **current working directory** unless an output path is supplied. `neb-movie` uses a positional choice rather than argparse, so `-h` does not show its help.

### `align-neb` — align vacancy-migration endpoints

Start from a perfect structure and give the **zero-based** indices of the atoms whose sites are vacant in the initial and final states:

```powershell
CCkit align-neb POSCAR 12 35 -e O
```

The script removes both indexed atoms to form a common backbone, then inserts one atom at the same index in each endpoint. This keeps atom counts and ordering aligned for interpolation. Both indexed atoms must have the selected element (`O` by default), and at least one atom of that element must remain in the backbone. It writes `POSCAR0` and `POSCAR1` in the current working directory; `-o0` and `-o1` select other output paths. The terminal report includes the minimum-image separation between the two original sites.

### `make-neb` — interpolate NEB image structures

Interpolate between endpoint structures that have the same atom count, element order, and cell:

```powershell
CCkit make-neb POSCAR0 POSCAR1 -n 5 -t 0.5
```

`-n` sets the number of **intermediate** images (default 5). The example writes `00/POSCAR` through `06/POSCAR` in the current working directory, including both endpoints. Existing numbered directories are reused and their `POSCAR` files are replaced. The path uses periodic minimum-image interpolation without changing the lattice; `-t` is pymatgen's endpoint autosort tolerance in Å (default 0.5). The command also prints the sum of corresponding atoms' minimum-image endpoint displacements.

### `neb-movie` — collect NEB images into a trajectory

Run from a directory containing numeric image subdirectories:

```powershell
CCkit neb-movie 0
CCkit neb-movie 1
```

Choice `0` reads each `POSCAR`; choice `1` prefers `CONTCAR` and falls back to `POSCAR`. Directories are ordered numerically, missing structures are skipped with a warning, and periodic atoms are wrapped. The output is `movie.extxyz` in the current working directory, with each frame's image number stored as metadata. The command accepts exactly one argument, `0` or `1`; it does not implement an `-h` option.

### `png-to-mp4` — turn PNG files into a video

Run in the directory containing the PNG frames:

```powershell
CCkit png-to-mp4 -o neb_animation.mp4 -f 10
```

The command reads `*.png` only from the current working directory, sorting by the first number in each filename, and writes an MP4 with imageio. The default output is `animation.mp4` and the default frame rate is 1.5 frames/s. If no PNG files are found, it prints a message and creates no video.

## NEP training module: command reference

All six scripts in `Scripts/neptrain/` are registered. These commands prepare and label XYZ datasets, generate VASP single-point or EOS jobs, and compare DFT and NEP energies. `compare-neb` and `compare-eos` need calorine and a trained `nep.txt`; EOS fitting also needs pymatgen.

### `merge-xyz` — combine structure datasets

Read every frame from each input file in the listed order:

```powershell
CCkit merge-xyz train_a.xyz train_b.xyz -o combined.xyz
```

The result is written as extended XYZ, regardless of the output extension. The default output is `out.xyz` in the current working directory; an explicit `-o` path is used as supplied. Existing output files are replaced.

### `config-type` — label configurations

Add the same `Config_type` metadata value to all selected frames:

```powershell
CCkit config-type dataset.xyz bulk --slice 0:100
```

`--slice` uses ASE index/slice syntax and defaults to all frames. The default output is `<input-stem>_config_type.extxyz` beside the input file. `-o` selects a different path; a relative path is interpreted from the current working directory. The command writes extended XYZ and leaves the input file unchanged.

### `prepare-sp` — split an XYZ dataset into VASP structures

Convert each frame of an XYZ dataset into a numbered VASP calculation directory:

```powershell
CCkit prepare-sp -i train.xyz --out singlepoint
```

The input defaults to `train.xyz`; the output directory defaults to `singlepoint` in the current working directory. The script writes `singlepoint/0/POSCAR`, `singlepoint/1/POSCAR`, and so on without sorting atoms, then creates `singlepoint.zip` beside the directory. Existing numbered directories and their `POSCAR` files are reused and replaced. This command writes structures only; it does not copy `INCAR`, `POTCAR`, or job scripts.

### `eos-maker` — prepare and fit a VASP volume scan

Prepare volume-scaled VASP jobs, then fit completed calculations:

```powershell
CCkit eos-maker make CONTCAR
CCkit eos-maker fit .
```

`make` reads one optimized structure and, by default, creates 11 directories named `V_970` through `V_1020` **beside the input**. Their volume ratios span 0.97 to 1.02; each gets a scaled `POSCAR` plus copies of `INCAR-2` and `POTCAR` from beside the input. `--start`, `--stop`, and `--points` set the scan; `--incar` and `--potcar` select other source files. At least four points are required. Existing output directories cause an error unless `--overwrite` is given; that option replaces the three VASP input files within them.

`fit` reads final energy and volume from `V_*/OUTCAR` below the supplied directory, skipping folders without `OUTCAR`. It requires at least four valid, distinct volumes. It writes `EOS.dat`, `EOS_fit.txt`, `EOS_fit_curve.dat`, and `EOS.png` inside that directory using a Birch-Murnaghan fit. `--energy-offset` shifts only the plotted energy baseline; `--dpi` changes the plot resolution (default 600).

### `compare-neb` — compare DFT and NEP energy barriers

Read numeric NEB image folders containing `OUTCAR` (or `OUTCAR.gz`) and `CONTCAR` or `POSCAR`:

```powershell
CCkit compare-neb --neb ./neb_run --nep nep.txt --out barrier_comparison
```

For each image, the script reads the DFT energy from `OUTCAR` and evaluates NEP energy on `CONTCAR`, falling back to `POSCAR`. Both energy series are shifted by their first image's energy, and the terminal prints each maximum relative energy as a barrier. It writes `nebsample.xyz` in the NEB directory and `barrier_comparison.txt` plus `barrier_comparison.png` relative to the current working directory. Defaults are `--neb .`, `--nep nep.txt`, and output base name `EnergyBarrierDFTvsNEP`.

### `compare-eos` — compare DFT and NEP EOS curves

Read completed EOS calculations from `eos-maker`'s `V_*` subdirectories or legacy numeric subdirectories:

```powershell
CCkit compare-eos --eos ./eos_runs --nep nep.txt --out eos_comparison
```

Completed subdirectories need `OUTCAR` (or `OUTCAR.gz`) and `CONTCAR` or `POSCAR`; folders without these files are skipped. Other directory names are ignored. The script reads final DFT energy and volume from `OUTCAR`, computes NEP energy on the structure, converts each calculation to per-atom values, and fits Birch-Murnaghan curves. At least four completed calculations with distinct volumes are required. It prints equilibrium volumes in Å³/atom, bulk moduli in GPa, and minimum energies in eV/atom. It writes `eos_comparison.txt` and `eos_comparison.png` relative to the current working directory. Defaults are `--eos .`, `--nep nep.txt`, and output base name `EOS_DFT_vs_NEP`.

