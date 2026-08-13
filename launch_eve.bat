@echo off
title E.V.E. 3D Neural HUD Launcher
cd /d "%~dp0"

if exist "C:\Users\KIIT\AppData\Local\hermes\hermes-agent\venv\Scripts\activate.bat" (
    call "C:\Users\KIIT\AppData\Local\hermes\hermes-agent\venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

echo Starting E.V.E. 3D Cyberpunk Desktop App...
python main.py
