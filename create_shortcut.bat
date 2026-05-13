@echo off
set "SCRIPT_DIR=%~dp0"
set "START_DIR=%CD%"
cd /d "%SCRIPT_DIR%"
python SubpoenaHelper.py
if errorlevel 1 (
    pause
)
cd /d "%START_DIR%"
