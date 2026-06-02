@echo off
setlocal enabledelayedexpansion

REM Minecraft Mod Updater - One-Click Setup & Launcher
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

REM Check if venv exists
if not exist ".venv\Scripts\Activate.bat" (
  echo Setting up Minecraft Mod Updater...
  echo.
  echo Creating virtual environment...
  py -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
)

REM Install/update dependencies (using full venv path)
echo Installing dependencies...
.venv\Scripts\pip.exe install -q -r requirements.txt
if errorlevel 1 (
  echo Failed to install dependencies.
  pause
  exit /b 1
)

REM Launch GUI (using full venv path)
echo Starting Minecraft Mod Updater...
.venv\Scripts\pythonw.exe -m src.gui
