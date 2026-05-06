#!/bin/bash
#SBATCH --job-name=cuda_filter
#SBATCH --output=filter_%j.out
#SBATCH --partition=gpu_a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=8G
#SBATCH --time=01:00:00

echo "=== CUDA FILTER JOB ==="
echo "Host: $(hostname)"
echo "Date: $(date)"

# === CARICA MODULI ===
module purge
module load gcc/12.4.0
module load nvhpc-hpcx-2.20-cuda12/25.1

# === OPENCV CONFIG ===
OPENCV_DIR="$HOME/Fabiooni/software/opencv-install"
export LD_LIBRARY_PATH=$OPENCV_DIR/lib64:$LD_LIBRARY_PATH

# === COMPILAZIONE ===
echo "=== COMPILING CUDA FILTER ==="
nvcc filter.cu -O3 -o filter \
    -I$OPENCV_DIR/include/opencv4 \
    -L$OPENCV_DIR/lib64 \
    -lopencv_core -lopencv_imgproc -lopencv_imgcodecs -lopencv_highgui \
    -lstdc++ -lcudart

if [ ! -f "./filter" ]; then
    echo "✗ Compilation failed"
    exit 1
fi

# ======================================================
# === LOOP SU IMMAGINI, BLOCK SIZES + 10 RUN PER CONFIG ===
# ======================================================

echo "=== STARTING FULL EXPERIMENT ==="

FILTER_TYPE="gaussian"
ITERATIONS=1
BLOCK_SIZES="8 16 32"
IMAGES_DIR="./images"

images=$(ls $IMAGES_DIR/*.jpg $IMAGES_DIR/*.png 2>/dev/null)

if [ -z "$images" ]; then
    echo "ERROR: No images found in $IMAGES_DIR"
    exit 1
fi

for img in $images; do
    echo "============================================="
    echo " PROCESSING IMAGE: $img"
    
    # Estrazione del nome originale (Ground Truth) per il calcolo del PSNR
    # Se il file è "4K_50.jpg", estrae "4K". Se è "16K.jpg", estrae "16K".
    BASENAME=$(basename "$img")
    PREFIX=$(echo "$BASENAME" | cut -d'_' -f1 | cut -d'.' -f1)
    
    CLEAN_IMG="$IMAGES_DIR/${PREFIX}.jpg"
    
    # Se per caso le originali sono png, gestiamo il fallback
    if [ ! -f "$CLEAN_IMG" ]; then
        CLEAN_IMG="$IMAGES_DIR/${PREFIX}.png"
    fi
    
    echo " Reference Ground Truth: $CLEAN_IMG"
    echo "============================================="

    for bs in $BLOCK_SIZES; do
        echo ">> Testing Block Size: $bs <<"
        
        for run in $(seq 1 10); do
            # Salva l'immagine fisica su disco solo alla prima run
            if [ "$run" -eq 1 ]; then
                SAVE_FLAG=1
            else
                SAVE_FLAG=0
            fi
            
            # Parametri: noisy_img, clean_img, filter_type, block_size, iterations, save_flag
            srun ./filter "$img" "$CLEAN_IMG" "$FILTER_TYPE" $bs $ITERATIONS $SAVE_FLAG
        done
    done
done

echo "=== ALL RUNS FOR ALL IMAGES COMPLETED ==="

echo "=== JOB COMPLETED ==="
echo "Date: $(date)"
