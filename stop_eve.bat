@echo off
title Stop Eve Assistant
echo Stopping Eve AI Voice Assistant...

powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

echo [OK] Eve process terminated successfully.
timeout /t 2 >nul
