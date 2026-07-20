@echo off
cd /d "%~dp0"
title Desktop Livestream - live view
echo Starting live perception viewer (screen + OCR + voice)...
"C:/Users/m808b/AppData/Local/Programs/Python/Python312/python.exe" "%~dp0run_live.py"
echo.
echo Stopped. Press any key to close.
pause >nul
