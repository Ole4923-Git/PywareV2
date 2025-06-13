@echo off
SETLOCAL
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    set "PYTHON_URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
    set "PYTHON_INSTALLER=python-installer.exe"
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"
    if exist "%PYTHON_INSTALLER%" (
        start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del "%PYTHON_INSTALLER%"
    ) else (
        pause
        exit /b 1
    )
)
python -m ensurepip --default-pip
python -m pip install --upgrade pip
pip install discord.py pillow mss opencv-python sounddevice numpy scipy pyautogui pynput screeninfo requests psutil pycaw comtypes pywin32 mss numpy scipy
cls
python build.py
exit
