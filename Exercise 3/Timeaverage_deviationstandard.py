import os
import re
import numpy as np
import matplotlib.pyplot as plt

desktop = os.path.join(os.path.expanduser("~"), "Desktop")

# Elenco delle cartelle da processare: (nome_cartella, etichetta_per_legenda)
folders_info = [
    ("1000_iterations", "1000 iterations"),
    ("2000_iterations", "2000 iterations"),
    ("3000_iterations", "3000 iterations"),
    ("5000_iterations", "5000 iterations"),
    ("10000_iterations", "10000 iterations"),
    # aggiungi altre cartelle qui se vuoi
]

# Regex per estrarre thread e runtime
pattern = re.compile(
    r"\[Perf Run\].*?(\d+)\s*threads.*?Runtime[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*seconds",
    re.DOTALL | re.IGNORECASE,
)

plt.figure(figsize=(9, 7))

for folder_name, label in folders_info:
    folder = os.path.join(desktop, "hpc", "Ex3", "Output_times simulazione 2", folder_name)
    if not os.path.isdir(folder):
        print(f"Cartella non trovata: {folder}")
        continue

    runtimes = {}
    all_files = sorted(os.listdir(folder))
    if not all_files:
        print(f"Nessun file nella cartella: {folder}")
        continue

    for filename in all_files:
        if not filename.lower().endswith(".out"):
            continue
        path = os.path.join(folder, filename)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            print(f"Impossibile leggere {filename}: {e}")
            continue

        matches = pattern.findall(text)
        if not matches:
            print(f"Nessuna corrispondenza in: {filename}")
            continue

        for threads, runtime in matches:
            try:
                threads_i = int(threads)
                runtime_f = float(runtime.replace(",", "."))
            except Exception:
                print(f"Parsing fallito in {filename}: threads={threads}, runtime={runtime}")
                continue
            runtimes.setdefault(threads_i, []).append(runtime_f)

    if not runtimes:
        print(f"Nessun runtime estratto per {label}")
        continue

    threads_sorted = sorted(runtimes.keys())
    means = [np.mean(runtimes[t]) for t in threads_sorted]
    # stds = [np.std(runtimes[t]) for t in threads_sorted]  # non serve per il grafico

    # Plot solo la media, senza std
    plt.plot(threads_sorted, means, marker="o", label=label)

plt.title("Execution Time vs Number of Threads for Different Iterations")
plt.xlabel("Number of Threads")
plt.ylabel("Execution Time (seconds)")
plt.grid(True)
plt.legend()
plt.show()

print("\nSummary Table (mean ± std and speedup for each iteration group):\n")
header = ["Iteration Group", "Threads", "Mean (s)", "Std Dev (s)", "Speedup (vs prev)"]
print(f"{header[0]:<18} | {header[1]:<7} | {header[2]:<12} | {header[3]:<12} | {header[4]:<16}")
print("-" * 80)

for folder_name, label in folders_info:
    folder = os.path.join(desktop, "hpc", "Ex3", "Output_times simulazione 2", folder_name)
    if not os.path.isdir(folder):
        continue

    runtimes = {}
    all_files = sorted(os.listdir(folder))
    if not all_files:
        continue

    for filename in all_files:
        if not filename.lower().endswith(".out"):
            continue
        path = os.path.join(folder, filename)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            continue

        matches = pattern.findall(text)
        if not matches:
            continue

        for threads, runtime in matches:
            try:
                threads_i = int(threads)
                runtime_f = float(runtime.replace(",", "."))
            except Exception:
                continue
            runtimes.setdefault(threads_i, []).append(runtime_f)

    if not runtimes:
        continue

    threads_sorted = sorted(runtimes.keys())
    means = [np.mean(runtimes[t]) for t in threads_sorted]
    stds = [np.std(runtimes[t]) for t in threads_sorted]

    prev_mean = None
    for t, m, s in zip(threads_sorted, means, stds):
        if prev_mean is not None:
            speedup = prev_mean / m
            speedup_str = f"{speedup:.2f}"
        else:
            speedup_str = "-"
        print(f"{label:<18} | {t:<7} | {m:<12.4f} | {s:<12.4f} | {speedup_str:<16}")
        prev_mean = m
