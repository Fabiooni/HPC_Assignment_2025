# HPC Assignment 2024-2025

This repository contains the source code, final report, and data analysis for the High Performance Computing assignment.

### Authors:
- F. Garrone (S349449)
- L. Lo Brutto (S346285)
- A. Ruggieri (S341930)

---

## Repository Structure
The repository is organized as follows:

- `/Exercise 2/` - Source code for Exercise 2 (Multi-dimensional Image Processing in CUDA)
  - `filter.cu` / `filter_windows.cu`: Main CUDA implementations.
  - `Data_analysis.py`: Python script for evaluating execution performance and resource usage.
  - `Compile.bat`, `run.sh`, `run_all_windows.bat`: Automation and execution scripts for Unix/Windows.
  - `/Plot/`: Contains generated SVG graphs and LaTeX statistics tables evaluating block size impact and PSNR degradation.
- `/Report/` - Contains the IEEE format Final Report.
  - `main.pdf`: Compiled final report.
  - `main.tex`, `main.fdb_latexmk`: LaTeX source files.
  - `/OPEN_MP/`, `/CUDA/`, `/svg-inkscape/`: LaTeX assets and figures.

*(Note: Exercises 1 and 3, along with the presentation slides, will be included in their respective folders).*

## Environment & Prerequisites
The code was developed and tested across Unix and Windows environments. 
To compile and run the programs, the following tools are required:
- **C Compiler:** `gcc/11.5.0`
- **MPI:** `3.3.1`
- **CUDA:** `CUDA 12` (Tested on Local CUDA 25.1 and Legion `hpc-x-2.21`)
- **OpenMP:** `OpenMP 4.5`
- **Python 3:** Required to run `Data_analysis.py` for performance evaluation.

---

## Quick Start & Compilation Guide.

### Exercise 1: MPI (Systolic array for matrix multiplication)
[cite_start]This exercise implements a systolic array structure to compute matrix multiplication across distributed nodes. 
To compile the generator, build the MPI executable, generate the initial input matrices, and submit the SLURM job to the `edu_sapphire` partition:
```bash
cd "Exercise 1"
# Execute the wrapper script to compile and submit the job
./run_experiments_500.sh
./run_experiments_1000.sh
./run_experiments_2000.sh
# the diff script run 500x500 for thread 1,2,3,4,5,6,7 and 8
./run_experiments_500_dif.sh
python3 data_presentation.py 
```

### Exercise 2: CUDA (Multi-dimensional data processing)
**Data Note:** Due to GitHub file size limits, the raw 4K, 8K, and 16K test images (including `pexels-christian-heitz.jpg`) are not tracked in this repository. Ensure your test images are available locally before running the scripts.

**Unix/Linux:**
```bash
cd "Exercise 2"
# Execute the shell script to compile and run the CUDA filter
bash run.sh
```

**Windows:**
```
cd "Exercise 2"
# Compile the Windows-specific source
Compile.bat
# Run the batch script to process the images
run_all_windows.bat
```
### Exercise 3: OpenMP (Heat Diffusion Simulation)

``` bash
cd "Exercise 3"
# Submit the SLURM job (loads gcc/12.4.0, compiles with OpenMP, and runs the simulation)
# goroup A for half hot hal cold
sbatch run_Ex3_a_1000.sbatch
sbatch run_Ex3_a_2000.sbatch
sbatch run_Ex3_a_3000.sbatch
sbatch run_Ex3_a_5000.sbatch
# group B for hot center and cold surround
sbatch run_Ex3_b_1000.sbatch
sbatch run_Ex3_b_2000.sbatch
sbatch run_Ex3_b_3000.sbatch
sbatch run_Ex3_b_5000.sbatch

```