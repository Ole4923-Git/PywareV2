@echo off
SETLOCAL

:: Set temporary environment variable to find Python if it's not in PATH
set "TEMPORARY_PATH=%PATH%"

:: Try to find Python and install required modules
where python >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo Python is installed, now installing required modules...
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
    pip install discord.py pillow mss opencv-python sounddevice numpy scipy pyautogui pynput screeninfo requests psutil pycaw comtypes pywin32 mss numpy scipy
    cls
    python build.py
    exit
)

:: If Python is not found
echo Python not found in system. Installing Python first...

set "PYTHON_URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
set "PYTHON_INSTALLER=python-installer.exe"

echo Downloading Python installer...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"

if exist "%PYTHON_INSTALLER%" (
    echo Installing Python in the background...
    start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del "%PYTHON_INSTALLER%"
    
    echo Python has been installed. Now installing required modules...
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
    pip install discord.py pillow mss opencv-python sounddevice numpy scipy pyautogui pynput screeninfo requests psutil pycaw comtypes pywin32 mss numpy scipy
    cls
    python build.py
) else (
    echo Error: Failed to download Python installer.
    pause
    exit /b 1
)

exit
