@echo off
title Beatstar AI - Servidor Original (Renacer)
cd /d "%~dp0"
echo ========================================================
echo       Iniciando Servidor Beatstar AI (Renacer)
echo       Direccion: http://127.0.0.1:8000
echo ========================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
    "%USERPROFILE%\.local\bin\uv.exe" run python run.py
) else (
    python run.py
)
pause
