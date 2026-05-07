#!/bin/bash
#SBATCH --job-name=heat_diffusion_a
#SBATCH --output=heat_a.out
#SBATCH --error=heat_a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:00:10
#SBATCH --mem=4G

module purge
module load gcc/12.4.0
gcc Ex3.c -o Ex3 -fopenmp -O3
./Ex3 input_a.txt output_a.txt 1024 1024 0.2 0.3 3000
