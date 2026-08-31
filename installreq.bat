@echo off
title YLCCV Requirements Installer

:Check
echo - Checking for Python...
where python >nul
if errorlevel 1 (
  echo Python not installed or in the PATH. Checking py...
  where py >nul
  if errorlevel 1 (
    echo The command "py" don't exist. Installing Python...
    goto InstallPython
  )
  echo The command "py" exists. Checking if pip is included...
  where pip >nul
  if errorlevel 1 (
    echo PIP needs to be used with py. Installing requirements with py...
    goto InstallReqs.py
  )
  echo PIP is included. Installing requirements with pip...
  goto InstallReqs.pip
)
echo Python is installed! Checking for pip...
where pip >nul
if errorlevel 1 (
  echo PIP needs to be used with Python. Installing requirements with python...
  goto InstallReqs.python
)
echo PIP exists.
goto InstallReqs.pip

:InstallPython
echo.
echo Installing Python...
mkdir %temp%\YTLCCV
cd %temp%\YTLCCV
curl -o PyInstall.exe https://www.python.org/ftp/python/3.14.7/python-3.14.7-amd64.exe
if errorlevel 1 (
  echo FAIL: Couldn't download Python.
  pause
  exit
)
start "" /wait "PyInstaller.exe" /quiet InstallAllUsers=1 PrependPath=1
echo Python Installed! Rechecking...
echo.
goto Check

:InstallReqs.py
echo.
echo - Checking requirements...
py -m pip install -r requirements.txt
goto Finish

:InstallReqs.python
echo.
echo - Checking requirements...
python -m pip install -r requirements.txt
goto Finish

:InstallReqs.pip
echo.
echo - Checking requirements...
pip install -r requirements.txt
goto Finish

:Finish
echo.
echo The requirements have been installed succesfully!
pause
