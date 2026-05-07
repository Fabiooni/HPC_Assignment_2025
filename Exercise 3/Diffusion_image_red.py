import os
import numpy as np
from PIL import Image

desktop = os.path.join(os.path.expanduser("~"), "Desktop")

# Cartelle fisse (modifica i nomi se vuoi)
INPUT_DIR = os.path.join(desktop,"hpc", "Ex3", "Input_immaginidiffusione")         # cartella con file di valori (sull aScrivania)
OUTPUT_DIR = os.path.join(desktop,"hpc", "Ex3", "Immagini simulazione 2")  # cartella di destinazione per le immagini

# Controlli e creazione cartelle
if not os.path.exists(INPUT_DIR):
    raise SystemExit(f"Cartella input non trovata: {INPUT_DIR}\nMetti i tuoi file in questa cartella sul Desktop.")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Raccogli tutti i file regolari nella cartella input, ordinati
all_files = sorted([f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))])
if not all_files:
    raise SystemExit(f"Nessun file trovato in {INPUT_DIR}")

def infer_shape_from_length(n):
    # prova quadrato, altrimenti trova una coppia di fattori vicina alla radice
    side = int(np.sqrt(n))
    if side * side == n:
        return side, side
    for r in range(side, 0, -1):
        if n % r == 0:
            return r, n // r
    return 1, n  # fallback

def load_numeric_array(path):
    # tenta a caricare con loadtxt; se fallisce ritorna None
    try:
        arr = np.loadtxt(path)
    except Exception:
        return None
    if arr is None:
        return None

    # usa float per la normalizzazione
    arr = np.array(arr, dtype=float)

    # Se arr è 2D già ok; se 1D inferisci forma
    if arr.ndim == 1:
        rows, cols = infer_shape_from_length(arr.size)
        arr = arr.reshape((rows, cols))
    elif arr.ndim == 2:
        pass
    else:
        # non gestito
        return None

    # Normalizza in 0-255:
    amin, amax = arr.min(), arr.max()
    if amax <= 1.0 and amin >= 0.0:
        # valori 0..1 -> scala a 0..255
        arr = arr * 255.0
    elif amax > 255 or amin < 0 or amax != amin:
        # se intervallo oltre 0..255 o negativo -> normalizza min-max
        if amax == amin:
            arr = np.clip(arr, 0, 255)
        else:
            arr = (arr - amin) / (amax - amin) * 255.0
    # clip e cast a uint8
    arr = np.clip(arr, 0, 255).round().astype(np.uint8)
    return arr

# Processa tutti i file e salva immagini numerate
count = 0
for idx, fname in enumerate(all_files, start=1):
    in_path = os.path.join(INPUT_DIR, fname)
    data = load_numeric_array(in_path)
    if data is None:
        print(f"Saltato (impossibile leggere): {fname}")
        continue
    h, w = data.shape
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :, 0] = data  # canale rosso
    image = Image.fromarray(img)

    out_name = f"{(idx)}.png"   # numerazione da 1 ... n (usa idx per corrispondenza con ordinamento)
    out_path = os.path.join(OUTPUT_DIR, out_name)
    try:
        image.save(out_path)
    except Exception:
        image.save(out_path, format="PNG")
    count += 1
    print(f"{count}: salvata -> {out_path}")

print(f"Completato: {count} immagini salvate in {OUTPUT_DIR}")

