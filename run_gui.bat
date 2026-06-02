@echo off
setlocal
cd /d %~dp0
if not exist ".venv\Scripts\Activate.bat" (
  echo Virtual environment not found. Run setup_and_run.bat first.
  pause
  exit /b 1
)
.venv\Scripts\pythonw.exe -m src.gui
