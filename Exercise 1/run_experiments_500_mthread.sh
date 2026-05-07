#!/bin/bash

# --- 1. PARAMETRI BASE DELL'ESPERIMENTO ---
N=500                  # Fissiamo a 500 per l'analisi del trade-off come da traccia
NODES=2                # Numero di nodi fisici (almeno 2 come da traccia)
TASKS_PER_NODE=2       # Processi MPI per nodo

# Array dei thread da testare per costruire la curva di saturazione
# Modifica questi valori in base ai core fisici massimi disponibili sui nodi edu_sapphire

# Paramiter
N=500                  # Matrix size
NODES=2                # No node (>1 request)
TASKS_PER_NODE=2       # No MPI proces
THREADS_ARRAY=(1 2 3 4 5 6 7 8) 
# Thread OpenMP per MPI 

TIMESTAMP=$(date +"%Y%m%d_%H%M")

MATA="MatA_${N}.csv"
MATB="MatB_${N}.csv"

MATC_RES="MatC_res_N${N}_nodes${NODES}_tasks${TASKS_PER_NODE}.csv"
OUT_FILE="report_${TIMESTAMP}_N${N}_nodes${NODES}.out"
ERR_FILE="report_${TIMESTAMP}_N${N}_nodes${NODES}.err"

module purge
module load mpich/3.3.1_gcc11  
gcc -O3 generatore.c -o generatore
if mpicc -O3 -fopenmp ES01.c -o cannon_exec -lm; then
    echo "Ok"
else
    echo "ERRORE: Compilat fail"
    exit 1
fi


if [ ! -f "$MATA" ]; then 
    ./generatore $N $MATA
fi
if [ ! -f "$MATB" ]; then 
    ./generatore $N $MATB
fi


# Iteriamo su ogni configurazione di thread
for THREADS in "${THREADS_ARRAY[@]}"; do
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    MATC_RES="MatC_res_N${N}_nodes${NODES}_tasks${TASKS_PER_NODE}_threads${THREADS}.txt"
    OUT_FILE="report_${TIMESTAMP}_N${N}_threads${THREADS}.out"
    ERR_FILE="report_${TIMESTAMP}_N${N}_threads${THREADS}.err"
    
    echo " job with ${THREADS} thread(s) per task..."
    
    sbatch \
        --partition=edu_sapphire \
        --job-name="cannon_N${N}" \
        --nodes=$NODES \
        --ntasks-per-node=$TASKS_PER_NODE \
        --cpus-per-task=$CPUS_PER_TASK \
        --output=$OUT_FILE \
        --error=$ERR_FILE \
        submit_cannon.sbatch $N $MATA $MATB $MATC_RES
    sleep 1
done
