#!/bin/bash
#SBATCH --time=00:10:00
#SBATCH --partition=cpu_sapphire

# Recuperiamo gli argomenti passati da sbatch alla fine della riga
N=$1
FILE_A=$2
FILE_B=$3
FILE_C=$4

module purge
module load mpich/3.3.1_gcc11

# --- NUOVA SEZIONE: COMPILAZIONE SUL NODO ---
# Compiliamo l'eseguibile direttamente sul nodo di calcolo.
# Usiamo -march=native per ottimizzare per le CPU Sapphire Rapids del nodo.
mpicc -O3 -fopenmp -march=native ES01.c -o cannon_exec -lm

# Verifichiamo che la compilazione sia andata a buon fine
if [ $? -ne 0 ]; then
    echo "ERRORE CRITICO: Compilazione fallita sul nodo di calcolo!"
    exit 1
fi
# --------------------------------------------

# Configuriamo OpenMP
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

# Calcoliamo i task totali
P=$SLURM_NTASKS

# --- INTESTAZIONE DEL REPORT ---
echo "========================================="
echo "       ESECUZIONE CANNON MATMUL          "
echo "========================================="
echo "Dimensione Matrice (N) : $N"
echo "Nodi Allocati          : $SLURM_NNODES"
echo "Task per Nodo          : $SLURM_NTASKS_PER_NODE"
echo "Task Totali MPI (P)    : $P"
echo "Thread OpenMP per Task : $OMP_NUM_THREADS"
echo "Core Totali Utilizzati : $(( P * OMP_NUM_THREADS ))"
echo "File Matrice A         : $FILE_A"
echo "File Matrice B         : $FILE_B"
echo "File Risultato         : $FILE_C"
echo "========================================="
echo "Inizio calcolo..."

# Registriamo il tempo di inizio
START_TIME=$(date +%s)

# Lancio dell'eseguibile
srun -n $P ./cannon_exec $N $FILE_A $FILE_B $FILE_C

# Registriamo il tempo di fine
END_TIME=$(date +%s)
echo "Calcolo terminato in $(( END_TIME - START_TIME )) secondi."
