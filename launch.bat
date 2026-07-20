@echo off
cd /d "%~dp0"
title Desktop Livestream - live view
echo Starting live perception viewer (screen + OCR + voice)...
python "%~dp0run_live.py"
echo.
echo Stopped. Press any key to close.
pause >nul
