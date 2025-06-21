@echo off
color 8
setlocal enabledelayedexpansion
title PywareV2 Installer
:check_installation
set "targetDir=%LOCALAPPDATA%\PywareV2"
set "installed=0"
if exist "%targetDir%" (
    if exist "%targetDir%\Main.py" (
        if exist "%targetDir%\Setup.cmd" (
            set "installed=1"
        )
    )
)
:menu
cls
echo Installation Status: 
if %installed%==1 (
    powershell -command "Write-Host 'PywareV2 is installed' -ForegroundColor Green"
) else (
    powershell -command "Write-Host 'PywareV2 is not installed' -ForegroundColor Red"
)
echo.
echo What do you want to do?
echo 01. Install
echo 02. Uninstall
echo 03. Update
echo 04. Open Builder
echo 05. Open Folder
echo 06. Join Discord
echo 07. Terms of service
echo 08. Exit
echo.
set /p choice="Enter your choice (1-8): "
if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto update
if "%choice%"=="4" goto openbuilder
if "%choice%"=="5" goto openfolder
if "%choice%"=="6" goto joindiscord
if "%choice%"=="7" goto Tos
if "%choice%"=="8" goto end
echo Invalid choice, please try again.
pause
goto menu
:joindiscord
start "" "https://discord.gg/BNaDKPrmaP"
goto menu
:install
cls
echo Installing PywareV2...
echo.
call :progress 0
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :progress 10 "Installing Python 3.11"
    
    set "tempDir=%TEMP%\PywareInstaller"
    if not exist "%tempDir%" mkdir "%tempDir%"
    
    call :progress 20 "Downloading Python"
    curl -L -o "%tempDir%\python-installer.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" >nul 2>&1
    if %errorlevel% neq 0 (
        cls
        echo Error downloading Python
        pause
        exit /b %errorlevel%
    )
    call :progress 40 "Installing Python"
    start /wait "" "%tempDir%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 >nul 2>&1
    del "%tempDir%\python-installer.exe"
)
call :progress 50 "Creating folders"
set "targetDir=%LOCALAPPDATA%\PywareV2"
if not exist "%targetDir%" mkdir "%targetDir%" >nul 2>&1
set "downloads[0].url=https://raw.githubusercontent.com/Ole4923-Git/PywareV2/main/build.py"
set "downloads[0].name=build.py"
set "downloads[1].url=https://raw.githubusercontent.com/Ole4923-Git/PywareV2/main/Setup.cmd"
set "downloads[1].name=Setup.cmd"
set "downloads[2].url=https://raw.githubusercontent.com/Ole4923-Git/PywareV2/main/Main.py"
set "downloads[2].name=Main.py"
set "downloads[3].url=https://github.com/Ole4923-Git/PywareV2/raw/main/Pyware.ico"
set "downloads[3].name=Pyware.ico"
set "downloads[4].url=https://github.com/Ole4923-Git/PywareV2/raw/main/EXE.ico"
set "downloads[4].name=EXE.ico"
set /a step=60
for /l %%i in (0,1,4) do (
    set /a step+=10
    call :progress !step! "Downloading !downloads[%%i].name!"
    curl -L -o "%targetDir%\!downloads[%%i].name!" "!downloads[%%i].url!" >nul 2>&1
    if !errorlevel! neq 0 (
        cls
        echo Error downloading !downloads[%%i].name!
        pause
        exit /b !errorlevel!
    )
)
call :progress 90 "Creating shortcut"
set "shortcut=%USERPROFILE%\Desktop\PywareV2-Setup.lnk"
set "target=%LOCALAPPDATA%\PywareV2\Setup.cmd"
set "icon=%LOCALAPPDATA%\PywareV2\Pyware.ico"
powershell -command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$s = $ws.CreateShortcut('%shortcut%'); " ^
    "$s.TargetPath = '%target%'; " ^
    "$s.WorkingDirectory = '%LOCALAPPDATA%\PywareV2'; " ^
    "$s.IconLocation = '%icon%'; " ^
    "$s.Save()" >nul 2>&1
set "installed=1"
call :progress 100 "Installation complete"
timeout /t 1 >nul
cls
echo Installation completed successfully!
pause
goto menu
:progress
setlocal
set "percent=%~1"
set "status=%~2"
if "%status%"=="" set "status=Working..."
set /a bars=percent/5
set "progressbar=["
for /l %%i in (1,1,20) do (
    if %%i leq %bars% (
        set "progressbar=!progressbar!#"
    ) else (
        set "progressbar=!progressbar! "
    )
)
set "progressbar=!progressbar!] %percent%%%"
if %percent% lss 25 (
    set "color=Red"
) else if %percent% lss 50 (
    set "color=DarkYellow"
) else if %percent% lss 75 (
    set "color=Yellow"
) else if %percent% lss 100 (
    set "color=Green"
) else (
    set "color=Green"
)
cls
echo Installing PywareV2...
echo.
for /f "delims=" %%a in ('powershell -command "Write-Host '[ ' -NoNewline; for($i=1;$i -le %bars%;$i++) { if ($i -le 5) { Write-Host '#' -ForegroundColor Red -NoNewline } elseif ($i -le 10) { Write-Host '#' -ForegroundColor DarkYellow -NoNewline } elseif ($i -le 15) { Write-Host '#' -ForegroundColor Yellow -NoNewline } else { Write-Host '#' -ForegroundColor Green -NoNewline } }; for($i=%bars%+1;$i -le 20;$i++) { Write-Host ' ' -NoNewline }; Write-Host ' ] %percent%%%' -NoNewline"') do (
    echo %%a
)
echo !status!
endlocal & exit /b
:uninstall
echo Uninstalling PywareV2...
set "targetDir=%LOCALAPPDATA%\PywareV2"
if exist "%USERPROFILE%\Desktop\PywareV2-Setup.lnk" (
    del "%USERPROFILE%\Desktop\PywareV2-Setup.lnk"
)
if exist "%targetDir%" (
    rmdir /s /q "%targetDir%"
    set "installed=0"
    cls
    echo PywareV2 successfully uninstalled.
) else (
    cls
    echo PywareV2 is not installed.
)
pause
goto menu
:update
cls
echo Updating PywareV2...
echo.
call :progress 0
set "targetDir=%LOCALAPPDATA%\PywareV2"
if not exist "%targetDir%" (
    cls
    echo PywareV2 is not installed. Please install first.
    pause
    goto menu
)
set "downloads[0].url=https://raw.githubusercontent.com/Ole4923-Git/PywareV2/main/build.py"
set "downloads[0].name=build.py"
set "downloads[1].url=https://raw.githubusercontent.com/Ole4923-Git/PywareV2/main/Setup.cmd"
set "downloads[1].name=Setup.cmd"
set "downloads[2].url=https://raw.githubusercontent.com/Ole4923-Git/PywareV2/main/Main.py"
set "downloads[2].name=Main.py"
set "downloads[3].url=https://github.com/Ole4923-Git/PywareV2/raw/main/Pyware.ico"
set "downloads[3].name=Pyware.ico"
set "downloads[4].url=https://github.com/Ole4923-Git/PywareV2/raw/main/EXE.ico"
set "downloads[4].name=EXE.ico"
set /a step=10
for /l %%i in (0,1,4) do (
    set /a step+=20
    call :progress !step! "Updating !downloads[%%i].name!"
    curl -L -o "%targetDir%\!downloads[%%i].name!" "!downloads[%%i].url!" >nul 2>&1
    if !errorlevel! neq 0 (
        cls
        echo Error updating !downloads[%%i].name!
        pause
        exit /b !errorlevel!
    )
)
call :progress 100 "Update complete"
timeout /t 2 >nul
cls
echo Update completed successfully!
pause
goto menu
:openbuilder
cls
echo Starting PywareV2 Builder...
set "targetDir=%LOCALAPPDATA%\PywareV2"
if not exist "%targetDir%" (
    echo PywareV2 is not installed. Please install first.
    pause
    goto menu
)
if not exist "%targetDir%\Setup.cmd" (
    echo Setup script not found.
    pause
    goto menu
)
cd /d "%targetDir%"
start "" "Setup.cmd"
goto menu
:openfolder
cls
set "targetDir=%LOCALAPPDATA%\PywareV2"
if not exist "%targetDir%" (
    echo PywareV2 is not installed. Please install first.
    pause
    goto menu
)
explorer "%targetDir%"
goto menu
:Tos
cls
echo ================================================
echo           PywareV2 Terms of Service
echo           Last Updated: 2025-06-10
echo ================================================
echo.
echo [ Acceptance of Terms ]
echo By using PywareV2 ("the Bot"), you agree to these Terms of Service.
echo If you do not agree, do not use or deploy the Bot.
echo.
echo [ Nature of the Software ]
echo PywareV2 is an open-source remote-control bot.
echo You are responsible for self-hosting and setup.
echo No hosting or backend is provided.
echo You are fully accountable for all actions performed by the Bot.
echo.
echo [ User Responsibility ]
echo You must NOT:
echo - Use the Bot for illegal, malicious, or unethical purposes.
echo - Gain unauthorized access to systems or devices.
echo - Deploy it on machines without explicit permission.
echo.
echo [ Disclaimer of Liability ]
echo PywareV2 is provided "as is" with no warranties.
echo The developers are not liable for damage, loss, or issues.
echo Use the Bot at your own risk.
echo.
echo [ Privacy and Data Handling ]
echo PywareV2 processes only local data for functionality.
echo No data is collected, sold, or shared.
echo Data handling is entirely local and under your control.
echo See the Privacy Policy for details.
echo.
echo [ Modifications and Termination ]
echo These Terms may change at any time without notice.
echo Misuse may result in revoked support access.
echo Use responsibly to retain access to community resources.
echo.
pause
goto menu
:end
echo Exiting...
exit