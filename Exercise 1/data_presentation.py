import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def extract_data():
    # List to accumulate data from all files
    all_results = []

    # Finds all files starting with 'report_' and ending in '.out'
    files = glob.glob("report_*.out")

    # Regex to capture specific Italian headers from the logs 
    re_n = re.compile(r"Dimensione Matrice \(N\) : (\d+)")
    re_p = re.compile(r"Task Totali MPI \(P\)    : (\d+)")
    re_t = re.compile(r"Thread OpenMP per Task : (\d+)")
    re_time = re.compile(r"Tempo di esecuzione: ([\d.]+) secondi")

    for filename in files:
        with open(filename, 'r') as f:
            content = f.read()
            
            # Parameter extraction
            n_val = re_n.search(content)
            p_val = re_p.search(content)
            t_val = re_t.search(content)
            
            # Execution time extraction (multiple occurrences per file) [cite: 2, 6, 8, 11, 14, 17]
            times = [float(t) for t in re_time.findall(content)]
            
            if n_val and p_val and t_val and times:
                # In HPC, the MAX time is often used as the bottleneck value
                max_time = max(times)
                avg_time = sum(times) / len(times)

                all_results.append({
                    "File": filename,
                    "N": int(n_val.group(1)),
                    "MPI_Tasks": int(p_val.group(1)),
                    "Threads": int(t_val.group(1)),
                    "Execution_Time_Max": max_time,
                    "Execution_Time_Avg": avg_time
                })

    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    # Sort by matrix size
    if not df.empty:
        df = df.sort_values(by="N")
    
    return df

# --- Execution ---
df_results = extract_data()
print("--- Extracted Data Table ---")
print(df_results.to_string(index=False))

# Save to CSV
df_results.to_csv("cannon_results.csv", index=False)

# --- Visualization Settings ---
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12})

# Group data by N and Threads to get clean averages across multiple runs
df_grouped = df_results.groupby(['N', 'Threads']).agg({
    'Execution_Time_Avg': 'mean',
    'Execution_Time_Max': 'mean'
}).reset_index()

# --- PLOT 1: Thread Scalability (N=500) ---
plt.figure(figsize=(10, 6))
df_500 = df_grouped[df_grouped['N'] == 500]

sns.lineplot(data=df_500, x='Threads', y='Execution_Time_Avg', marker='o', linewidth=2.5, color='royalblue')
plt.title('OpenMP Thread Scalability (500x500 Matrix)', fontsize=14, pad=15)
plt.xlabel('Number of Threads per MPI Task')
plt.ylabel('Average Execution Time (s)')
plt.xticks([1, 2, 4, 8]) 
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('thread_scalability_500.png')
plt.show()

# --- PLOT 2: Matrix Size Impact (Fixed Threads = 4) ---
plt.figure(figsize=(10, 6))
df_fixed_threads = df_grouped[df_grouped['Threads'] == 4]

sns.barplot(data=df_fixed_threads, x='N', y='Execution_Time_Avg', palette='viridis')
plt.title('Execution Time Comparison by Matrix Dimension (4 OpenMP Threads)', fontsize=14, pad=15)
plt.xlabel('Matrix Dimension (N x N)')
plt.ylabel('Average Execution Time (s)')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add data labels on top of the bars
for i, val in enumerate(df_fixed_threads['Execution_Time_Avg']):
    plt.text(i, val, f'{val:.4f}s', ha='center', va='bottom', fontweight='bold')

plt.savefig('matrix_dimension_comparison.png')
plt.show()