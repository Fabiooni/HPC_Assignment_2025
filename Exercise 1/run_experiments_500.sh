#!/bin/bash
#SBATCH --partition=edu_sapphire
#SBATCH --time=00:10:00

# Paramiter
N=500                  # Matrix size
NODES=2                # No node (>1 request)
TASKS_PER_NODE=2       # No MPI proces
CPUS_PER_TASK=4        # Thread OpenMP per MPI 

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


sbatch \
    --partition=edu_sapphire \
    --job-name="cannon_N${N}" \
    --nodes=$NODES \
    --ntasks-per-node=$TASKS_PER_NODE \
    --cpus-per-task=$CPUS_PER_TASK \
    --output=$OUT_FILE \
    --error=$ERR_FILE \
    submit_cannon.sbatch $N $MATA $MATB $MATC_RES

echo "Job result in: $OUT_FILE"