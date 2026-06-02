@echo off
setlocal
cd /d %~dp0
if not exist ".venv\Scripts\Activate.bat" (
  echo Virtual environment not found. Create it with:
  echo   python -m venv .venv
  pause
  exit /b 1
)
call ".venv\Scripts\Activate.bat"
pip install pyinstaller
pyinstaller --onefile --windowed --name MinecraftModUpdater src\gui.py
echo.
echo Done. Your executable is in the dist folder:
echo   dist\MinecraftModUpdater.exe
pause
