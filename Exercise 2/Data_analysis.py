import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import glob
import re
import os

# ==========================================
# 1. SETUP E RICERCA FILE AUTOMATICA
# ==========================================
mia_palette_ieee = ['#2df788', '#fffb1f', '#16c8d9', '#401fff', '#CCB974']

def get_resolution(name):
    if '16K' in name: return '16K'
    elif '8K' in name: return '8K'
    elif '4K' in name: return '4K'
    return 'Unknown'

def get_noise_level(name):
    if '_50' in name: return '50%'
    elif '_75' in name: return '75%'
    elif '_90' in name: return '90%'
    return 'Original'

# Cerchiamo i file del cluster
csv_files = glob.glob('execution_times_*_GPU.csv')

# Aggiungiamo il file della RTX se presente nella cartella
if os.path.exists('execution_times_RTX_2060.csv'):
    csv_files.append('execution_times_RTX_2060.csv')

if not csv_files:
    print("Nessun file CSV trovato per l'analisi.")
    exit()

all_data = []

# ==========================================
# 2. CICLO SU OGNI FILE TROVATO
# ==========================================
for file in csv_files:
    # Logica di Parsing Dinamica per Cluster vs Windows
    if 'RTX_2060' in file:
        hw_label = 'RTX 2060 Mobile'
        file_pref = 'RTX2060'
        sort_idx = 0  # Ordiniamo la RTX per prima come baseline
    else:
        match = re.search(r'execution_times_(\d+)_GPU\.csv', file)
        if not match: continue
        num = int(match.group(1))
        hw_label = f'{num} A100'
        file_pref = f'{num}A100'
        sort_idx = num

    print(f"\n--- Elaborazione file: {file} ({hw_label}) ---")
    
    df = pd.read_csv(file, header=None)
    df.columns = ['Filename', 'Time_ms', 'PSNR_dB', 'Filter', 'BlockSize', 'Kernel', 'Iterations', 'Timestamp']
    
    df['Resolution'] = df['Filename'].apply(get_resolution)
    df['Noise'] = df['Filename'].apply(get_noise_level)
    df['HW_Label'] = hw_label
    df['Sort_Idx'] = sort_idx
    
    all_data.append(df)
    
    # ------------------------------------------
    # GRAFICO 1: TEMPO DI ESECUZIONE vs BLOCK SIZE
    # ------------------------------------------
    time_stats = df.groupby(['Resolution', 'BlockSize'])['Time_ms'].mean().unstack()
    time_stats = time_stats.reindex(['4K', '8K', '16K'])
    
    fig, ax = plt.subplots(figsize=(10, 6), layout='constrained')
    time_stats.plot(kind='bar', ax=ax, width=0.4, color=mia_palette_ieee, edgecolor='black')
    
    ax.set_title(f'Impact of Thread Block Size on Execution Time ({hw_label})\n(Average over 10 runs)', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('Execution Time (ms)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Image Resolution', fontsize=12, fontweight='bold')
    ax.legend(title='Block Size (Threads)', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', padding=3, fontsize=9, fontweight='bold')
        
    plt.xticks(rotation=0, fontsize=11)
    plt.savefig(f'Plot_1_{file_pref}_BlockSize_Impact.svg', format='svg', bbox_inches='tight')
    plt.close()

    # ------------------------------------------
    # GRAFICO 2: DEGRADO DEL PSNR vs RUMORE
    # ------------------------------------------
    psnr_stats = df.groupby(['Resolution', 'Noise'])['PSNR_dB'].mean().unstack()
    psnr_stats = psnr_stats[['Original', '50%', '75%', '90%']]
    psnr_stats = psnr_stats.reindex(['4K', '8K', '16K'])
    
    fig, ax = plt.subplots(figsize=(10, 6), layout='constrained')
    psnr_stats.plot(kind='bar', ax=ax, width=0.4, color=mia_palette_ieee, edgecolor='black')
    
    ax.set_title(f'Filter Effectiveness: PSNR Degradation vs Impulse Noise ({hw_label})', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('PSNR (dB) - Higher is Better', fontsize=12, fontweight='bold')
    ax.set_xlabel('Image Resolution', fontsize=12, fontweight='bold')
    ax.legend(title='Noise Level', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', padding=3, fontsize=9, fontweight='bold')
        
    plt.xticks(rotation=0, fontsize=11)
    plt.savefig(f'Plot_2_{file_pref}_PSNR_Degradation.svg', format='svg', bbox_inches='tight')
    plt.close()

    # ------------------------------------------
    # GRAFICO 3: DETERMINISMO HARDWARE
    # ------------------------------------------
    df_bs32 = df[df['BlockSize'] == 32]
    if not df_bs32.empty:
        noise_time_stats = df_bs32.groupby(['Resolution', 'Noise'])['Time_ms'].agg(['mean', 'std']).reset_index()
        df_16k = noise_time_stats[noise_time_stats['Resolution'] == '16K'].set_index('Noise')
        
        if not df_16k.empty:
            df_16k = df_16k.reindex(['Original', '50%', '75%', '90%'])
            
            fig, ax = plt.subplots(figsize=(8, 5), layout='constrained')
            ax.errorbar(df_16k.index, df_16k['mean'], yerr=df_16k['std'], fmt='-o', 
                        color='#1f77b4', linewidth=2, capsize=5, markersize=8)
            
            ax.set_title(f'Execution Time Stability Across Noise Levels\n(16K Image, Block=32, {hw_label})', fontsize=13, fontweight='bold', pad=15)
            ax.set_ylabel('Execution Time (ms)', fontsize=11, fontweight='bold')
            ax.set_xlabel('Impulse Noise Density', fontsize=11, fontweight='bold')
            
            min_val = (df_16k['mean'] - df_16k['std']).min()
            max_val = (df_16k['mean'] + df_16k['std']).max()
            buffer = (max_val - min_val) * 0.5 if (max_val - min_val) != 0 else 5
            ax.set_ylim(max(0, min_val - buffer), max_val + buffer)
            
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.set_axisbelow(True)
            plt.savefig(f'Plot_3_{file_pref}_SIMD_Determinism.svg', format='svg', bbox_inches='tight')
            plt.close()

# ==========================================
# 3. GRAFICI 4: SCALABILITÀ HARDWARE (A100 vs RTX)
# ==========================================
if len(all_data) > 0:
    print("\n--- Generazione Grafici Comparativi Hardware ---")
    df_all = pd.concat(all_data, ignore_index=True)
    
    # Estraiamo l'ordine logico (RTX -> 1 A100 -> 2 A100 -> 3 A100)
    ordered_labels = df_all[['Sort_Idx', 'HW_Label']].drop_duplicates().sort_values('Sort_Idx')['HW_Label'].tolist()
    
    for bs in [8, 16, 32]:
        df_bs = df_all[df_all['BlockSize'] == bs]
        if df_bs.empty: continue
        
        comp_stats = df_bs.groupby(['Resolution', 'HW_Label'])['Time_ms'].mean().unstack()
        # Riordiniamo le colonne con il nostro ordine logico
        comp_stats = comp_stats.reindex(columns=[col for col in ordered_labels if col in comp_stats.columns])
        comp_stats = comp_stats.reindex(['4K', '8K', '16K'])
        
        fig, ax = plt.subplots(figsize=(10, 6), layout='constrained')
        markers = ['o', 's', '^', 'D', 'v']
        
        for idx, hw in enumerate(comp_stats.columns):
            # Diamo uno stile tratteggiato alla RTX per farla risaltare come baseline
            line_style = '--' if 'RTX' in hw else '-'
            ax.plot(comp_stats.index, comp_stats[hw], 
                    marker=markers[idx % len(markers)], linestyle=line_style, linewidth=2.5, markersize=8, 
                    label=hw)
            
        ax.set_title(f'Hardware Execution Time Scaling vs Resolution\n(Average over 10 runs, Block Size = {bs} Threads)', fontsize=14, fontweight='bold', pad=15)
        ax.set_ylabel('Execution Time (ms)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Image Resolution', fontsize=12, fontweight='bold')
        ax.legend(title='Hardware Configuration', fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.savefig(f'Plot_4_Hardware_Comparison_BS{bs}.svg', format='svg', bbox_inches='tight')
        plt.close()

# ==========================================
# 4. EXPORT STATISTICO PER LATEX
# ==========================================
    print("\n--- Generazione file LaTeX (statistics_table.tex) ---")
    
    df_report = df_all[df_all['BlockSize'] == 32]
    stats_table = df_report.groupby(['Resolution', 'HW_Label'])['Time_ms'].agg(['mean', 'var']).unstack('HW_Label')
    stats_table = stats_table.reindex(['4K', '8K', '16K'])

    tex_filename = "statistics_table.tex"
    with open(tex_filename, "w") as f:
        f.write("% NOTA: Richiede il pacchetto \\usepackage{booktabs} nel preambolo\n")
        f.write("\\begin{table}[htbp]\n")
        f.write("    \\centering\n")
        f.write("    \\caption{Hardware Scalability Analysis: Mean Execution Time, Variance, and Relative Speedup (Block Size $32\\times32$)}\n")
        f.write("    \\label{tab:hw_scalability}\n")
        f.write("    \\begin{tabular}{lccc}\n")
        f.write("        \\toprule\n")
        f.write("        \\textbf{Hardware} & \\textbf{Mean Time (ms)} & \\textbf{Variance (ms$^2$)} & \\textbf{Speedup} \\\\\n")
        f.write("        \\midrule\n")

        for res in stats_table.index:
            f.write(f"        \\multicolumn{{4}}{{c}}{{\\textbf{{Resolution: {res}}}}} \\\\\n")
            f.write("        \\midrule\n")
            
            # La baseline per lo speedup è sempre la 1 A100 (se esiste)
            base_time = stats_table.loc[res, ('mean', '1 A100')] if '1 A100' in stats_table['mean'].columns else None
            
            for hw in ordered_labels:
                if hw not in stats_table['mean'].columns: continue
                
                mean_val = stats_table.loc[res, ('mean', hw)]
                var_val  = stats_table.loc[res, ('var', hw)]
                
                if not np.isnan(mean_val):
                    if base_time and not np.isnan(base_time):
                        speedup = base_time / mean_val
                        speedup_str = f"{speedup:.2f}$\\times$"
                    else:
                        speedup_str = "N/A"
                    
                    f.write(f"        {hw} & {mean_val:.2f} & {var_val:.2f} & {speedup_str} \\\\\n")
            
            if res != stats_table.index[-1]:
                f.write("        \\midrule\n")

        f.write("        \\bottomrule\n")
        f.write("    \\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"File '{tex_filename}' generato con successo!")
    print("Analisi completata.")