@echo off
REM T-MEDNet launcher (Windows)
REM Double-click this file to start the application.

cd /d "%~dp0"

REM Try activating the local venv if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python main.py
pause
