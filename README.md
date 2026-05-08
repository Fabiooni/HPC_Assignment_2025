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

## Quick Start & Compilation Guide

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
