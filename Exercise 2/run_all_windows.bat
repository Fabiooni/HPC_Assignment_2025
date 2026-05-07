@echo off
setlocal enabledelayedexpansion

echo === AVVIO TEST BATCH SU RTX 2060 ===

REM Cartella dove risiedono le immagini (rispetto al percorso corrente)
set IMAGES_DIR=images
set FILTER_TYPE=gaussian
set ITERATIONS=1
set BLOCK_SIZES=8 16 32

REM Controlla se l'eseguibile esiste
if not exist "filter_windows.exe" (
    echo ERRORE: filter_windows.exe non trovato. Devi prima compilare.
    pause
    exit /b
)

REM Ciclo su TUTTE le immagini JPG o PNG
for %%F in (%IMAGES_DIR%\*.jpg %IMAGES_DIR%\*.png) do (
    set "NOISY_IMG=%%F"
    
    REM Estrazione logica del prefisso per trovare l'originale
    for /f "tokens=1 delims=_" %%P in ("%%~nF") do (
        set "PREFIX=%%P"
    )
    
    REM Cerca il Ground Truth originale corrispondente (.jpg o .png)
    set "CLEAN_IMG=%IMAGES_DIR%\!PREFIX!.jpg"
    if not exist "!CLEAN_IMG!" (
        set "CLEAN_IMG=%IMAGES_DIR%\!PREFIX!.png"
    )

    echo.
    echo ==========================================================
    echo PROCESSAMENTO: !NOISY_IMG!
    echo GROUND TRUTH : !CLEAN_IMG!
    echo ==========================================================

    REM Doppio Loop: Per ogni Block Size, esegui 10 run
    for %%B in (%BLOCK_SIZES%) do (
        echo [!] Testing Block Size: %%B
        
        for /L %%R in (1, 1, 10) do (
            REM Flag di salvataggio (Salva fisicamente l'immagine solo alla prima run)
            if %%R equ 1 (
                set SAVE_FLAG=1
            ) else (
                set SAVE_FLAG=0
            )

            REM Richiamo dell'eseguibile CUDA per Windows
            filter_windows.exe "!NOISY_IMG!" "!CLEAN_IMG!" "%FILTER_TYPE%" %%B %ITERATIONS% !SAVE_FLAG!
        )
    )
)

echo.
echo === TUTTE LE ESECUZIONI COMPLETATE ===
pause