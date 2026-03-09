@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo python not found; please install Python 3.10+ and add it to PATH.
  exit /b 1
)

python dev_start.py --open

