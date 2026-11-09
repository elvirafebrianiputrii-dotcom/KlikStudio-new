@echo off
title KlikStudio - Sistem Pengelola Studio
cd /d "%~dp0"

echo ========================================================
echo             KLIKSTUDIO - SISTEM PENGELOLA
echo ========================================================
echo Membuka sistem KlikStudio...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    py -m streamlit run app.py
)

if errorlevel 1 (
    echo.
    echo Terjadi kendala saat menjalankan aplikasi.
    pause
)
