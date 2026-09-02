@echo off
setlocal EnableExtensions EnableDelayedExpansion
title YLCCV Requirements Installer

rem Put the requirements file to the same directory as this script
set "SCRIPT_DIR=%~dp0"
set "REQ_FILE=%SCRIPT_DIR%requirements.txt"

if not exist "%REQ_FILE%" (
  echo ERROR: requirements.txt not found at "%REQ_FILE%"
  pause
  exit /b 1
)

rem --- Ensure elevated privileges if installing system-wide Python ---
net session >nul 2>&1
if errorlevel 1 (
  echo Administrative privileges are required for a system Python install.
  echo Requesting elevation...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

rem --- Determine which python launcher to use (prefer py then python) ---
set "PYCMD="
where py >nul 2>&1 && set "PYCMD=py" || (
  where python >nul 2>&1 && set "PYCMD=python"
)

if defined PYCMD (
  echo Using %PYCMD% to install requirements from "%REQ_FILE%".
  echo Upgrading pip...
  %PYCMD% -m pip install --upgrade pip
  echo Installing requirements...
  %PYCMD% -m pip install -r "%REQ_FILE%"
  if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
  )
  echo.
  echo Requirements have been installed successfully!
  pause
  exit /b 0
)

rem --- No python found: download and run installer ---
echo Python not found on this machine. Downloading Python 3.14.7 (amd64) installer...
set "TMPDIR=%temp%\YTLCCV"
mkdir "%TMPDIR%" 2>nul
set "PYINSTALLER=%TMPDIR%\python-installer.exe"
set "PYURL=https://www.python.org/ftp/python/3.14.7/python-3.14.7-amd64.exe"

rem Try PowerShell first (most Windows have it), otherwise try curl if available
powershell -NoProfile -Command ^
  "try { Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYINSTALLER%'; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  where curl >nul 2>&1 && (
    curl -L -o "%PYINSTALLER%" "%PYURL%"
  )
)

if not exist "%PYINSTALLER%" (
  echo ERROR: Failed to download Python installer. Please download it manually:
  echo %PYURL%
  pause
  exit /b 1
)

echo Running Python installer (silent)...
start "" /wait "%PYINSTALLER%" /quiet InstallAllUsers=1 PrependPath=1
if errorlevel 1 (
  echo WARNING: Python installer returned an error code. Please run the installer manually if needed.
  pause
  exit /b 1
)

echo Python installation attempted. Re-checking for python...
rem Re-run this script (it will now take the PYCMD branch above)
"%~f0"
exit /b 0
