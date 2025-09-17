@echo off
setlocal enabledelayedexpansion

:: Always log to build_log.txt
set LOGFILE=build_log.txt
echo =============================== > %LOGFILE%
echo   🚀 Minecraft Fixer Build Tool >> %LOGFILE%
echo =============================== >> %LOGFILE%
echo. >> %LOGFILE%

:: Debug: Current folder
echo [DEBUG] Current folder: %cd% >> %LOGFILE%

:: Step 1: Find latest script
set "LATEST="
for /f "delims=" %%f in ('dir /b /a:-d /o:-n minecraft_fixer_update*.py 2^>nul') do (
    set "LATEST=%%f"
    goto found
)

:found
if not defined LATEST (
    echo ❌ No versioned script found. >> %LOGFILE%
    goto end
)

echo ✅ Found latest script: %LATEST% >> %LOGFILE%

:: Step 2: Cleanup
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist __pycache__ rd /s /q __pycache__

:: Step 3: Run PyInstaller
where pyinstaller >> %LOGFILE% 2>&1
if %errorlevel%==0 (
    echo 🛠 Running PyInstaller... >> %LOGFILE%
    pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." "!LATEST!" >> %LOGFILE% 2>&1
) else (
    echo ⚠ PyInstaller not in PATH, trying fallback... >> %LOGFILE%
    py -m PyInstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." "!LATEST!" >> %LOGFILE% 2>&1
)

:: Step 4: Rename EXE
for %%i in ("!LATEST!") do set "NAME=%%~ni"
if exist dist (
    cd dist
    for %%j in (*.exe) do (
        echo [DEBUG] Found build output: %%j >> ..\%LOGFILE%
        ren "%%j" "%NAME%.exe"
    )
    cd ..
)

:: Step 5: Done
if exist dist\%NAME%.exe (
    echo 🎉 Build succeeded! EXE is dist\%NAME%.exe >> %LOGFILE%
) else (
    echo ❌ Build failed. >> %LOGFILE%
)

:end
echo. >> %LOGFILE%
echo Build finished. See build_log.txt for details.
pause
