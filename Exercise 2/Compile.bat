@echo off
echo === COMPILING CUDA FILTER ON WINDOWS (RTX 2060) ===

:: IMPOSTA LA DIRECTORY DI OPENCV (Punta alla cartella 'build')
set OPENCV_DIR=C:\Program Files\Opencv\build

:: IMPOSTA IL NOME DELLA LIBRERIA OPENCV (Senza .lib alla fine)
:: Controlla in %OPENCV_DIR%\x64\vc16\lib come si chiama esattamente.
set OPENCV_LIB=opencv_world4110

echo OpenCV Directory: %OPENCV_DIR%
echo Compiling...

:: Esecuzione di nvcc con flag di ottimizzazione host/device e linking OpenCV
nvcc filter_windows.cu -O3 -o filter_windows.exe ^
    -I"%OPENCV_DIR%\include" ^
    -L"%OPENCV_DIR%\x64\vc16\lib" ^
    -l%OPENCV_LIB%

if %ERRORLEVEL% == 0 (
    echo.
    echo [OK] Compilation successful!
    echo Per eseguire: filter.exe "images\4K_50.jpg" "images\4K.jpg" "gaussian" 32 1 1
) else (
    echo.
    echo [ERROR] Compilation failed! Controlla i path di OpenCV.
)

pause