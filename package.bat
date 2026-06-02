@echo off
setlocal
cd /d %~dp0

REM Check if Python is available
py --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python is not installed or not in your PATH.
  echo.
  echo To fix this:
  echo 1. Install Python from https://www.python.org/downloads/
  echo 2. During installation, CHECK "Add Python to PATH"
  echo 3. Run this script again
  echo.
  pause
  exit /b 1
)

REM Build executable with PyInstaller
if not exist ".venv\Scripts\Activate.bat" (
  echo Virtual environment not found. Creating it...
  py -m venv .venv
)

.venv\Scripts\pip.exe install -q pyinstaller

echo Building executable...
.venv\Scripts\pyinstaller.exe --onefile --windowed --name MinecraftModUpdater ^
  --add-data "config.sample.json:." ^
  --add-data "requirements.txt:." ^
  --hidden-import=tkinter ^
  src\gui.py

if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo Build complete! Your executable is in: dist\MinecraftModUpdater.exe
echo.
echo To distribute:
echo 1. Copy dist\MinecraftModUpdater.exe
echo 2. Copy config.json (create from config.sample.json if needed)
echo 3. Users can now double-click MinecraftModUpdater.exe to run
echo.
pause
