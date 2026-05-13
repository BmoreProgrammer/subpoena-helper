@echo off
rem Creates a Desktop shortcut for SubpoenaHelper.py
rem Run this ONCE after setup.bat to create a desktop icon

set SCRIPT_DIR=%~dp0
set PYTHON=python

rem Try to find python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set PYTHON=py
)

rem Get absolute path to SubpoenaHelper.py
for %%i in ("%SCRIPT_DIR%SubpoenaHelper.py") do set TARGET="%%~fi"

rem Create desktop shortcut using PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Subpoena Helper.lnk'); $s.TargetPath = '%PYTHON%'; $s.Arguments = '""%SCRIPT_DIR%SubpoenaHelper.py""'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Description = 'Subpoena Helper - Process subpoenas locally'; $s.Save()"

if %ERRORLEVEL% equ 0 (
    echo Desktop shortcut created!
    echo Double-click the icon on your Desktop to start.
) else (
    echo Could not create shortcut.
    echo You can double-click SubpoenaHelper.py directly in this folder.
)

pause