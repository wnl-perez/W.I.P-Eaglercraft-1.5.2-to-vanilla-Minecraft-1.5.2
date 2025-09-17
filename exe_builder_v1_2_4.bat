@echo off
REM Minecraft Fixer EXE Builder (batch)
REM Usage: place this .bat in the same folder as minecraft_fixer_v1_2_4.py (and optional icon.ico), then double-click it.

SETLOCAL ENABLEDELAYEDEXPANSION

set "SCRIPT=minecraft_fixer_v1_2_4.py"
set "NAME=MinecraftFixer"
set "ICON=icon.ico"

echo --- EXE Builder for %SCRIPT% ---

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found in PATH. Please install Python 3.8+ and make sure 'python' is on your PATH.
  pause
  exit /b 1
)

:: Ensure pip and PyInstaller are present
echo Installing/upgrading build dependencies (pyinstaller, requests, nbtlib)...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
python -m pip install --upgrade pyinstaller requests nbtlib >nul 2>&1
if errorlevel 1 (
  echo Failed to install dependencies. Check your network or run the pip commands manually.
  pause
  exit /b 1
)

:: Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%NAME%.spec" del /q "%NAME%.spec"

:: Build command base
set "PYI_ARGS=--noconfirm --onefile --windowed --name %NAME% %SCRIPT%"

:: If icon exists, add it (PyInstaller expects Windows icon .ico)
if exist "%ICON%" (
  echo Using icon: %ICON%
  set "PYI_ARGS=--noconfirm --onefile --windowed --icon %ICON% --name %NAME% %SCRIPT%"
) else (
  echo No icon.ico found — building without custom icon.
)

echo Running PyInstaller...
python -m PyInstaller %PYI_ARGS%

if exist "dist\%NAME%.exe" (
  echo.
  echo Build Succeeded: dist\%NAME%.exe
  echo You can find the standalone EXE in the dist folder.
  pause
  exit /b 0
) else (
  echo.
  echo Build Failed. Check PyInstaller output above for errors.
  pause
  exit /b 2
)
