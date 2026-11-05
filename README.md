<!-- Begin section: Overview -->

# CCkit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/liubaoshuai1402/cckit)

A command-line toolkit for modeling, preparing, and analyzing crystal-structure calculations. CCkit brings common tasks in DFT, molecular dynamics, NEP machine-learning potentials, and NEB workflows together behind one launcher through small Python utilities.

## What CCkit provides

- **Structure modeling**: supercells, strain and rattling, substitutions, vacancies, and structural edits.
- **VASP workflow preparation**: single-point calculation folders, pre-relaxation INCAR settings, POSCAR cleanup and sorting, surface constraints, and OUTCAR comparison.
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
| template/&lt;script_name&gt; | Auxiliary templates grouped by core script filename without its extension |

## Installation

Use the lowercase command `cckit` on both Linux and Windows.

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

   ```bash
   export CCkit_PATHS="/your_dir_of_CCkit"
   export PATH="$CCkit_PATHS:$PATH"
   source "$CCkit_PATHS/cckit_completion.sh"
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

3. Add executable permissions to the `cckit` launcher:

   ```bash
   chmod +x "$CCkit_PATHS/cckit"
   ```

#### Windows user

---

Clone the repository or download the whole project. Set `CCkit_PATHS` to the repository directory (for example, `D:\your_dir_of_CCkit`) and add that same directory to your user `Path`.

Open a new terminal after changing these environment variables. The `cckit.bat` launcher runs Python from the active environment and accepts `cckit <command> ...` in both Command Prompt and PowerShell.

<img src="https://xiaoxiaobuaigugujiao.oss-cn-beijing.aliyuncs.com/img/cckit1.png"/>

Enable function-name completion in PowerShell (the equivalent of `source cckit_completion.sh` on Linux):

```powershell
. "D:\your_dir_of_CCkit\cckit_completion.ps1"
```

To make it take effect automatically in every new PowerShell session, add that line to your `$PROFILE`. The profile file may not exist yet on a fresh PowerShell installation, so create it first if needed:

```powershell
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force }
Add-Content -Path $PROFILE -Value '. "D:\your_dir_of_CCkit\cckit_completion.ps1"'
```

If loading the script is blocked by the execution policy, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

After that, type `cckit fix-` and press Tab to complete function names (works in PowerShell 7 and Windows PowerShell 5.1).

#### Updating an existing installation

The launcher and completion files are now named `cckit`, `cckit.bat`, `cckit_completion.sh`, and `cckit_completion.ps1`. Update completion paths in `~/.bashrc` or `$PROFILE`, then open a new terminal. Existing Linux scripts that invoke `CCkit` must use `cckit`, because Linux command names are case-sensitive.

The repository directory can keep its current name. Existing `CCkit_PATHS` and `PATH` settings remain valid.

## Usage

CCkit provides both a menu mode and a command-line mode.

Run `cckit` without arguments to open the interactive menu.

### Command-line usage

List all registered commands:

```powershell
cckit --listall
```

Command names and their script mappings are defined in `tools.json`. The launcher locates the mapped script under `CCkit_PATHS` and forwards the remaining arguments to it.

Check a command's help message before running it:

```powershell
cckit generate-strain -h
cckit dft-to-nep -h
```

General command-line form:

```powershell
cckit <function> <arguments>
```

### Highlights

- **Build structures** — create supercells, defects, substitutions, and strained configurations.
- **Prepare and inspect VASP jobs** — set up calculations and inspect ionic-step energies and forces, convergence, stress, and atomic displacements.
- **Prepare NEP datasets** — convert DFT results, label configurations, and split training data.
- **Fit equations of state** — generate volume scans and compare DFT and NEP curves.
- **Analyze trajectories** — explore hydrogen states, vacancies, bonds, and atomic clusters.
- **Estimate grain-boundary segregation** — calculate average solute concentrations from enthalpy and entropy data.
- **Study migration barriers** — prepare NEB images and compare DFT and NEP energy barriers.

### Example workflows

Generate strained and rattled structures:

```powershell
cckit generate-strain prim.xyz 0.005 10 10 2 -o strained.xyz
```

Prepare VASP single-point calculations from a trajectory:

```powershell
cckit convert-xyz-sp trajectory.xyz --submit vasp.pbs
```

Build an NEP dataset from VASP calculations:

```powershell
cckit dft-to-nep --pos ./vasp_calculations
cckit split-dataset dataset.xyz --valid_ratio 0.1 --test_ratio 0.1 --shuffle
```

Generate NEB images between two structures:

```powershell
cckit make-neb POSCAR_initial POSCAR_final -n 5
```

Prepare an EOS volume scan, then fit the completed calculations:

```powershell
cckit eos-maker make CONTCAR
cckit eos-maker fit .
```

Check the final cell stress and pressure after VASP relaxation:

```powershell
cckit check-stress
```

Estimate the average grain-boundary solute concentration:

```powershell
cckit seg-cal enthalpy_entropy.csv 0.01 --temperature 1000 --energy-unit eV
```

See the module references below for options, file requirements, and output details.

## VASP module: command reference

Prepare inputs, constrain structures, and inspect VASP results. Use `cckit <command> -h` for options.

### `convert-xyz-sp` — trajectory to single-point jobs

Turn trajectory frames into numbered VASP jobs. The trajectory must include cell information.

```powershell
cckit convert-xyz-sp trajectory.xyz
cckit convert-xyz-sp trajectory.xyz --submit vasp.pbs
cckit convert-xyz-sp trajectory.xyz --slice 500::100 --submit vasp.pbs --KPOINTS
```

Writes sorted structures to `singlepoint/<frame>/POSCAR` beside the trajectory; existing job directories are rejected. If `INCAR` is present there, also provide `POTCAR` and the `--submit` script; `--KPOINTS` includes the k-point file. The last example selects every 100th frame from frame 500.

### `convert-vasp-sp` — sample ionic steps into single-point jobs

Extract ionic structures from `OUTCAR`, `vasprun.xml` (also named `vasp.xml`), or `XDATCAR` using ASE:

```powershell
cckit convert-vasp-sp ../OUTCAR1 --interval 3 -o singlepoint1 --format outcar
cckit convert-vasp-sp ./run/vasprun.xml --interval 10 --submit vasp.pbs --KPOINTS
```

Sampling starts at the first ionic structure: `--interval 10` selects steps 1, 11, 21, …; the default interval is 1. By default, writes consecutive jobs to `<current-directory>/singlepoint/0/POSCAR`, `1/POSCAR`, …, preserving atom and element order, each frame's cell, and constraints available to ASE. **XDATCAR does not store constraints.** `.gz` inputs are accepted; renamed files require `--format outcar`, `xml`, or `xdatcar`. The final summary reports the total structures read, sampling interval, number converted to POSCAR, and output directory.

`INCAR` and `POTCAR` are checked independently in the command's working directory: each existing file is copied into every job, and missing files are skipped. `--submit` selects a submission script (relative paths resolve from the working directory), and `--KPOINTS` selects the local `KPOINTS`; each is copied only if it exists, independently of the other files. The input trajectory's directory is not searched for calculation inputs. With no files to copy, only POSCARs are written. Copied inputs are unchanged, so any INCAR should be suitable for single-point calculations.

Existing output directories are refused. All relative `-o` paths resolve from the command's working directory, including bare names; absolute paths are honored. The first example therefore creates `./singlepoint1/` where the command is run. If reading or writing fails partway through, already written jobs remain in the output directory.

### `prepare-vasp-batch` — distribute inputs to existing POSCAR directories

Copy shared inputs into existing calculation subdirectories containing `POSCAR`.

```powershell
cckit prepare-vasp-batch --root ./calculations --job vasp.pbs
```

The root supplies `INCAR`, `POTCAR`, and optional `KPOINTS` and job script. Searches recursively below the root and **replaces existing input copies**, keeping each `POSCAR`.

### `pre-relax` — prepare a short initial relaxation

Ease the initial relaxation of manually built magnetic structures by loosening INCAR settings:

```powershell
cckit pre-relax
cckit pre-relax D:/calculations/run/INCAR
```

Renames the original input to `INCAR-back` beside it, then writes a new INCAR with `EDIFF = 5E-05`, `NSW = 5`, `PREC = N`, and `KSPACING = 0.25`. **All four active parameters must already exist**; missing parameters or an existing backup cause an error before any file changes. `ISPIN` is retained as supplied.

An uncommented `ADDGRID` set to true (`.TRUE.`, `TRUE`, `.T.`, or `T`, case-insensitive) gets a `#` immediately before its name. Missing, false, or already commented settings stay unchanged. If other parameters follow it on the same line, a line break is inserted after the separating semicolon to keep them active.

Otherwise only the four required parameter values are replaced; line order, whitespace, comments, and line endings are preserved. Tags are case-insensitive, and all active duplicates are handled. Target values must be on one line. No third-party dependencies are required. Prepares the input only; run VASP separately.

### `fix-surface` — constrain a fractional-z interval

Fix atoms whose fractional z coordinate falls in `[ZMIN, ZMAX)`; atoms outside that interval remain free. For example, this fixes the lower part of a slab:

```powershell
cckit fix-surface POSCAR --zrange 0.0 0.3
```

Writes `POSCAR_fixed` beside the input, preserving atom order. Use `-o` for another output.

### `fix-interface` — keep the middle region movable

Fix atoms with fractional z < Z1 or z >= Z2; atoms in `[Z1, Z2)` remain free. This is useful when two outer interface regions should be constrained:

```powershell
cckit fix-interface POSCAR --z1 0.2 --z2 0.8
```

Requires `0 <= Z1 < Z2 <= 1`. Writes `POSCAR_fixed` beside the input, preserving atom order; `-o` selects another output.

### `sort-poscar` — order atoms by element

Specify the desired element order after `-s`:

```powershell
cckit sort-poscar POSCAR -s Zr Y O -o POSCAR_sorted
```

Unlisted elements follow the requested ones. Defaults to `POSCAR_sorted` in the current directory. **Atom indices change with the new order.**

### `vasp-displacement` — inspect relaxation displacements

Compare corresponding atoms in the initial `POSCAR` and relaxed `CONTCAR`:

```powershell
cckit vasp-displacement
cckit vasp-displacement ./run/POSCAR ./run/CONTCAR --top 5
```

Reports total displacement and the largest movers in Å, using periodic minimum-image distances and zero-based indices. `--top` sets the number shown (default 10). Inputs must have matching atom counts and element order.

### `compare-vasp-ef` — compare two OUTCAR results

Use two calculations of the same atom-ordered structure, for example to inspect an energy cutoff or k-point change:

```powershell
cckit compare-vasp-ef ./test-a/OUTCAR ./test-b/OUTCAR
```

Prints energy and force differences alongside `ENCUT` and `NKPTS`. Force indices are one-based; the stress row is a scaled comparison metric, **not a physical stress value**.

### `check-convergence` — scan OUTCAR files

Check calculation directories recursively:

```powershell
cckit check-convergence --root ./calculations
cckit check-convergence --root ./calculations --no-recursive
```

Lists calculations with VASP's ionic convergence marker. `--no-recursive` limits the scan to immediate subdirectories; the root's own `OUTCAR` is excluded. This marker alone does not establish electronic convergence or normal termination.

### `inspect-energy` — follow ionic relaxation energies

Plot the energy of each completed **ionic step**, plus the change between adjacent steps, while a relaxation is running:

```powershell
cckit inspect-energy ./run/OSZICAR
cckit inspect-energy ./run/OUTCAR --watch 5 --show
```

Writes `energy_vs_step.png` at 600 dpi beside the input; `-o` selects another PNG/PDF/SVG path, with bare filenames kept beside the input. Existing plots are replaced. A directory (default: `.`) prefers `OSZICAR`, then `OUTCAR`; `.gz` inputs are accepted. Requires matplotlib plus pymatgen for OSZICAR or ASE for OUTCAR.

Defaults to **F / TOTEN** (eV per cell); `--energy E0` selects sigma→0 energy. Steps start at 1 in completed-record order, excluding electronic iterations and unfinished trailing records. The lower panel shows signed adjacent-step energy changes in eV on a linear axis with scientific-notation tick labels. Energy trends alone do not establish force convergence.

`--watch` refreshes every 5 seconds unless specified, saving when energies change; Ctrl+C retains the plot. `--show` opens a GUI window; closing it stops monitoring. Omit `--show` on a headless server. See `-h` for other options, including renamed input files.

### `inspect-force` — follow maximum atomic forces

Track the largest atomic force at each completed **ionic step** of a relaxation:

```powershell
cckit inspect-force ./run/OUTCAR
cckit inspect-force ./run/OUTCAR --component total --watch 5 --show
```

By default, plots four curves in **eV/Å**: `max |Fx|`, `max |Fy|`, `max |Fz|`, and `max sqrt(Fx² + Fy² + Fz²)`, each maximum taken over all atoms independently. `--component x/y/z/total` selects one curve. Uses raw OUTCAR forces, including fixed atoms; OSZICAR is not supported. Requires ASE and matplotlib.

Writes `force_vs_step.png` at 600 dpi beside the input; `-o` selects another PNG/PDF/SVG path, with bare filenames kept beside the input. Existing plots are replaced. Accepts `OUTCAR.gz` or a directory containing `OUTCAR` (then `OUTCAR.gz`). Steps start at 1 in completed-record order; incomplete trailing force tables or ionic summaries are excluded.

`--watch` refreshes every 5 seconds unless specified, saving when maxima change; Ctrl+C retains the plot. Add `--show` for a GUI window, or omit it on a headless server. Closing the window stops monitoring.

### `check-stress` — report final cell stress

Read the final cell stress and pressure from `OUTCAR`, `OUTCAR.gz`, or a calculation directory:

```powershell
cckit check-stress
cckit check-stress ./run/OUTCAR.gz
cckit check-stress ./run --threshold 0.1
```

Defaults to local `OUTCAR`; reports stress, pressure, and shear in **GPa**, with compression positive. `--threshold` screens cell stress only for explicit `ISIF=3/6` and zero `PSTRESS`; it is not a convergence test. With `ISIF=1`, only external pressure is reliable.

### `reset-vasp` — preview and confirm directory cleanup

Run this **inside the directory to clean**:

```powershell
cckit reset-vasp -h
cckit reset-vasp 0
cckit reset-vasp 0 -remain CONTCAR vasp.pbs
```

**Preview → confirm → clean.** Mode `0` lists every file to delete: enter `y` to proceed or `n` to cancel. No arguments or `-h` shows help only.

Keeps directories and files starting with `INCAR`, `KPOINTS`, `POSCAR`, or `POTCAR`. Add `-remain` to keep extra exact filenames, as shown above. **All other files in the current directory are permanently deleted after confirmation.**

## Model module: command reference

Build and edit crystal structures. Atom indices are **zero-based**; output locations are noted below.

### `generate-strain` — strained and rattled training structures

Expand a dataset with random strains and atomic rattling:

```powershell
cckit generate-strain prim.xyz 0.005 10 10 2 --seed 1214
```

This example produces 40 variants per frame with strain components within ±0.005. Writes `rattled_strain_structures.xyz` in the current directory, or the `-o` path. Requires hiphive; use `--seed` for reproducibility.

### `generate-ysz` — substitution and vacancies together

Generate doped structures with vacancies in one step:

```powershell
cckit generate-ysz POSCAR Zr Y 10 O 3 --seed 1214
```

Here, 10 Zr atoms become Y and five O atoms are removed, producing three variants per frame. `--N2` overrides the vacancy count. Writes `ysztype.xyz` in the current directory.

### `generate-vacancy` — random vacancies

Delete `N` randomly selected atoms of one element and generate `M` variants from a **single** input structure:

```powershell
cckit generate-vacancy POSCAR O 2 5 --seed 1214
```

Writes `vacancy_structures.xyz` in the current directory; use `-o` for another output.

### `generate-substitute` — random substitutions

Replace `N` randomly selected atoms of element A with B and generate `M` variants from a **single** input structure:

```powershell
cckit generate-substitute POSCAR Zr Y 2 5 --seed 1214
```

Writes `substituted.xyz` in the current directory; use `-o` for another output. For substitutions plus vacancies, use `generate-ysz`.

### `generate-sol` — enumerate ordered doping arrangements

Use pymatgen and enumlib to enumerate symmetry-distinct arrangements after replacing a specified number of host atoms with a dopant:

```powershell
cckit generate-sol POSCAR Y 2 --host Zr --max_structures 100
```

Writes numbered `POSCAR` files to `Y2_structures/` in the current directory for this example. Requires pymatgen and enumlib; `--max_structures` limits the output count.

### `atat-sqs` — prepare fixed-cell SQS jobs

Generate ATAT inputs and a Slurm script for substitutional SQS, keeping the cell and atomic sites fixed:

```powershell
cckit atat-sqs POSCAR --solute Nb=1 Fe=1
cckit atat-sqs POSCAR --host Zr --solute Nb=2 Fe=3 Mo=1 --partition cpu1
```

`ELEMENT=COUNT` sets how many host atoms to replace. Multi-element inputs require `--host`; use a right-handed cell.

For Zr64, the first example creates `SQS_Zr62Nb1Fe1/` beside the input; existing output directories are refused. Copy it to a Linux/Slurm cluster, enter it, and run `sbatch run_sqs.sh`. The result is `runs/slurm_<jobid>_seed_<seed>/POSCAR_sqs`.

Requires Python 3.10+, NumPy and pymatgen locally and on the cluster, plus cluster-side ATAT 3.52 or a compatible version supporting `-ms`. See the generated `README.md` for setup and options. **Assess SQS quality with `bestcorr.out`; `SUCCESS` only confirms workflow and structure checks.**

### `supercell` — repeat a crystal cell

Repeat one input structure by integer factors along its three cell vectors:

```powershell
cckit supercell POSCAR 2 2 2 --output supercell.xyz
```

Reads one structure; defaults to `supercell.xyz` in the current directory.

### `add-atom` — place one atom by position or geometry

Choose one of four modes. `position` uses Cartesian coordinates, `center` uses the midpoint of two indexed atoms, `tricenter` uses the centroid of three indexed atoms, and `OH` places an atom beyond O along the M-to-O direction:

```powershell
cckit add-atom POSCAR --mode position --position 1.0 2.0 3.0 --element H
cckit add-atom POSCAR --mode center --atomA 0 --atomB 1
cckit add-atom POSCAR --mode tricenter --atomA 0 --atomB 1 --atomC 2 --element H
cckit add-atom POSCAR --mode OH --M 0 --O 1 --distance 1.0
```

Defaults to H and a 1.0 Å distance for `OH`. Indices are **0-based**. `tricenter` requires three distinct atoms and selects periodic images so **all three edges simultaneously have their minimum-image distances**, respecting the input cell and PBC, including skew cells. Equal-distance images are considered; if no compatible triangle exists, it raises an error. The centroid is wrapped into the periodic cell without moving the original atoms.

The `tricenter` example writes `POSCAR_tricenter_0_1_2` beside the input. `--output` changes the base name, keeping the geometry suffix; bare names are also placed beside the input, while paths containing a directory are honored as given.

### `remove-atom` — remove indexed atoms

Remove one or more atoms by index, optionally sorting the remaining elements with `-s`:

```powershell
cckit remove-atom POSCAR 0 3 -s Zr O
```

Writes `POSCAR_removed_0_3` beside the input. `-o` changes the base name; indices are still appended.

### `substitute-atom` — replace indexed atoms

Replace one or more indexed atoms with the element supplied to `-e`; `-s` optionally sorts the result by element:

```powershell
cckit substitute-atom POSCAR 3 5 -e Y -s Zr Y O
```

Writes `POSCAR_replaced_Y_3_5` beside the input. `-o` changes the base name; the element and indices are still appended.

### `move-crystal` — move a selected atom to the origin

Bring one selected atom to the origin and wrap the whole structure into the periodic cell:

```powershell
cckit move-crystal POSCAR 0 --output POSCAR_shifted
```

Defaults to `POSCAR_shifted_atom0` in the current directory.

### `line-dimer` — add two atoms on a line

Take the midpoint of two indexed atoms and append two atoms at `+r` and `-r` along their connecting line:

```powershell
cckit line-dimer POSCAR 0 1 --type_dimer H --r 0.37
```

Defaults to H with a 0.74 Å dimer separation (`2r`). Writes `dimer_added.xyz` in the current directory; `--output` selects another file.

## GPUMD module: command reference

Prepare NEP datasets and process GPUMD results. NEP relaxation requires calorine and a trained potential.

### `dft-to-nep` — collect VASP results into an XYZ dataset

Recursively find `OUTCAR` files under a calculation directory and read **all frames** from each one:

```powershell
cckit dft-to-nep --pos ./vasp_calculations --output dataset.xyz
```

Collects energies, forces, and stress into extended XYZ. Defaults to searching the current directory and writing `dataset.xyz` there.

### `split-dataset` — make train, validation, and test sets

Split every frame of an ASE-readable dataset into three XYZ files:

```powershell
cckit split-dataset dataset.xyz --valid_ratio 0.1 --test_ratio 0.1 --shuffle --seed 1214
```

Defaults to 5% validation and 5% test data. Use `--shuffle --seed` for a reproducible random split. **Replaces** `train.xyz`, `valid.xyz`, and `test.xyz` in the current directory.

### `relax-nep` — optimize a structure with an NEP potential

Use calorine's CPU NEP calculator to relax one structure:

```powershell
cckit relax-nep -i POSCAR --nep nep.txt --isif 3 --steps 200 --fmax 0.01
```

Use `--isif 3` to relax atoms and cell, or `--isif 2` for a fixed cell. Defaults to 200 FIRE steps and a 0.01 eV/Å force target. Writes `relaxed.xyz`, `energy.txt`, `POSCAR_relaxed`, and `log.out` in the current directory.

### `average-cell` — average an NPT cell

Read `model.xyz` and `thermo.out` from one GPUMD NPT directory:

```powershell
cckit average-cell --nptdir ./npt_run
```

Scales the structure into the mean cell and writes `model_temp.xyz` in the NPT directory. **All rows are averaged**; remove equilibration data first if needed.

### `average-stress` — average NPT stress components

Read `thermo.out` from one GPUMD NPT directory:

```powershell
cckit average-stress --nptdir ./npt_run
```

Writes six mean stress components to `stress.txt` in the NPT directory, with signs reversed and original units retained. **All rows are averaged.**

### `group-type` — label XYZ atoms by element

Add a per-atom integer `group` array to every `.xyz` or `.extxyz` file directly inside a folder:

```powershell
cckit group-type ./xyz
cckit group-type ./xyz --order O Zr H Y
```

Uses one element-to-ID mapping across the folder and writes `*_group.xyz` / `*_group.extxyz` beside each source. IDs start at zero; `--order` sets element priority. Existing outputs require `--overwrite`; subdirectories are skipped.

## Analysis module: command reference

Explore bonds, hydrogen, vacancies, clusters, and segregation. Bond, hydrogen, and vacancy analyses need cell information. Outputs go to the **current directory** unless noted otherwise.

### `global-bond` — bond lengths across a trajectory

Collect distances from each atom of element A to neighboring atoms of element B within a cutoff, across **all frames** of an ASE-readable input:

```powershell
cckit global-bond trajectory.extxyz O Zr 2.8
cckit global-bond trajectory.extxyz O Zr 2.8 --plt
```

Writes all, short, and long bond distances to `*bands_dis_global.txt`; `--plt` adds KDE data and plots. Short/long windows are fixed at 1.80–2.20 Å and >2.20–2.60 Å, independent of the search cutoff.

### `local-bond` — bond lengths near hydrogen

For each H atom, find nearby A atoms within `cutoff1`, then measure their A–B bonds within `cutoff2`:

```powershell
cckit local-bond trajectory.extxyz O Zr 1.2 2.8
```

Writes `*bands_dis_local.txt`; `--plt` adds KDE data and plots. Uses the same short/long windows as `global-bond`. **Only the final frame is saved for trajectory input.**

### `hydrogen-state` — classify hydrogen in each frame

Count H bonded to O, isolated interstitial H, and other H with nearby atoms:

```powershell
cckit hydrogen-state trajectory.extxyz --OHdist 1.2 --r 2.0
```

`--OHdist` sets the O–H bonding cutoff; `--r` distinguishes isolated H from H with other neighbors. Writes per-frame counts and averages to `count_H_state.txt` and `count_H_state_avg.txt`.

### `hydrogen-vacancy` — count isolated hydrogen

Despite the command name, this script counts H atoms with **no neighboring atom** within a radius; it does not locate vacant H sites:

```powershell
cckit hydrogen-vacancy trajectory.extxyz --r 1.8
```

Writes per-frame counts and their mean to `count_H_vacancy.txt` and `count_H_vacancy_avg.txt`. The default radius is 1.8 Å.

### `cluster-connect` — scan fragmentation against distance

See how the fraction of fragmented frames changes with the connection cutoff:

```powershell
cckit cluster-connect --input dump.xyz --species H --min 1.5 --max 5.0 --points 25 --sampling_interval 10 --plot
```

Writes cutoff (Å) versus fragmented-frame percentage to `fragmentation_vs_cutoff.txt`; `--plot` adds a PNG. A frame is fragmented when the selected element forms more than one cluster, using periodic distances.

### `cluster-size` — summarize cluster sizes

Use one cutoff to count connected clusters of a selected element in sampled frames:

```powershell
cckit cluster-size --input dump.xyz --species H --cutoff 2.0 --sampling_interval 10
```

Writes cluster counts, size statistics, and the pooled size distribution to `cluster_statistics_<cutoff>.txt`. Connections use periodic distances below the cutoff; frames without the selected element are skipped.

### `find-vacancy` — locate missing element sites

Compare a defect-free reference with a defective structure or trajectory. Oxygen is the default element:

```powershell
cckit find-vacancy reference.extxyz defective.extxyz
cckit find-vacancy reference.extxyz defective.extxyz --method ws --tolerance 1.2
```

Choose density deficits (default) or reference-site matching (`--method ws`). Writes `oxygen_vacancies.extxyz` with `X` markers and `oxygen_vacancies.csv` with coordinates. Use `-o` / `--report` for other paths, or `--cores` to process frames in parallel. **Density peaks are candidate sites, not guaranteed vacancies.**

### `seg-cal` — average grain-boundary segregation concentration

Read paired segregation enthalpy and entropy values from two columns of a text or CSV file:

```powershell
cckit seg-cal enthalpy_entropy.csv 0.01 --temperature 1000 --energy-unit eV
```

Here, `0.01` is the bulk solute fraction and `1000` is temperature in K. Enthalpy and `T × entropy` must match `--energy-unit` (`eV` or `kJ/mol`). Writes the mean concentration and fit parameters to `<input-stem>_segregation.json` beside the input.

### `atom_displacement.py` — unfinished helper

Unfinished and **not available as a command**: lacks a CLI and a required NumPy import.

## NEB module: command reference

Prepare migration paths and visualize NEB images. Outputs go to the **current directory** unless specified. `neb-movie` accepts `0` or `1` rather than `-h`.

### `align-neb` — align vacancy-migration endpoints

Start from a perfect structure and give the **zero-based** indices of the atoms whose sites are vacant in the initial and final states:

```powershell
cckit align-neb POSCAR 12 35 -e O
```

Writes atom-aligned endpoints to `POSCAR0` and `POSCAR1`; use `-o0` / `-o1` for other paths. Both selected sites must contain the chosen element, with at least one more atom of that element remaining.

### `make-neb` — interpolate NEB image structures

Interpolate between endpoint structures that have the same atom count, element order, and cell:

```powershell
cckit make-neb POSCAR0 POSCAR1 -n 5 -t 0.5
```

`-n 5` creates five intermediate images plus the endpoints: `00/POSCAR` through `06/POSCAR`. Uses periodic minimum-image interpolation; `-t` sets endpoint autosort tolerance in Å. **Existing image POSCARs are replaced.**

### `neb-movie` — collect NEB images into a trajectory

Run from a directory containing numeric image subdirectories:

```powershell
cckit neb-movie 0
cckit neb-movie 1
```

`0` collects POSCARs; `1` prefers CONTCARs, falling back to POSCARs. Writes `movie.extxyz` in numeric image order, skipping missing structures.

### `png-to-mp4` — turn PNG files into a video

Run in the directory containing the PNG frames:

```powershell
cckit png-to-mp4 -o neb_animation.mp4 -f 10
```

Combines local PNGs in filename-number order. `-f` sets frames per second; defaults to `animation.mp4` at 1.5 fps.

## NEP training module: command reference

Organize training data and compare DFT with NEP. Comparison commands require calorine and a trained potential; EOS fitting also needs pymatgen.

### `merge-xyz` — combine structure datasets

Read every frame from each input file in the listed order:

```powershell
cckit merge-xyz train_a.xyz train_b.xyz -o combined.xyz
```

Writes extended XYZ; defaults to `out.xyz` in the current directory. **Existing output is replaced.**

### `config-type` — label configurations

Add the same `Config_type` metadata value to all selected frames:

```powershell
cckit config-type dataset.xyz bulk --slice 0:100
```

Labels all frames by default; the example selects frames 0–99. Writes `<input-stem>_config_type.extxyz` beside the input; `-o` selects another path.

### `prepare-sp` — split an XYZ dataset into VASP structures

Convert each frame of an XYZ dataset into a numbered VASP calculation directory:

```powershell
cckit prepare-sp -i train.xyz --out singlepoint
```

Writes `singlepoint/<frame>/POSCAR` and `singlepoint.zip` in the current directory. Creates structures only; use `prepare-vasp-batch` to add calculation inputs. **Existing numbered POSCARs are replaced.**

### `eos-maker` — prepare and fit a VASP volume scan

Prepare volume-scaled VASP jobs, then fit completed calculations:

```powershell
cckit eos-maker make CONTCAR
cckit eos-maker fit .
```

`make` creates 11 volume-scaled jobs (0.97–1.02) beside the input, using local `INCAR-2` and `POTCAR`. Existing directories require `--overwrite`.

After VASP finishes, `fit` reads `V_*/OUTCAR` and writes EOS data, fit parameters, and `EOS.png` in the calculation root. Requires at least four distinct volumes; uses a Birch-Murnaghan fit.

### `compare-neb` — compare DFT and NEP energy barriers

Read numeric NEB image folders containing `OUTCAR` (or `OUTCAR.gz`) and `CONTCAR` or `POSCAR`:

```powershell
cckit compare-neb --neb ./neb_run --nep nep.txt --out barrier_comparison
```

Plots both energy profiles relative to their first image and reports the barriers. The example writes `barrier_comparison.txt` and `.png` in the current directory, plus `nebsample.xyz` in the NEB directory.

### `compare-eos` — compare DFT and NEP EOS curves

Read completed EOS calculations from `eos-maker`'s `V_*` subdirectories or legacy numeric subdirectories:

```powershell
cckit compare-eos --eos ./eos_runs --nep nep.txt --out eos_comparison
```

Compares fitted equilibrium volumes, bulk moduli, and per-atom energies. Each job needs `OUTCAR` (or `OUTCAR.gz`) and `CONTCAR` or `POSCAR`; at least four distinct volumes are required. The example writes `eos_comparison.txt` and `.png` in the current directory.

