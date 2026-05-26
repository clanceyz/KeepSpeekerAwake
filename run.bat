@echo off
REM Keep Speaker Awake - Launcher
REM Runs the application without showing a console window

cd /d "%~dp0"

set "LOG=%~dp0app.log"

if exist "%~dp0venv\Scripts\pythonw.exe" (
    start "" cmd /c ""%~dp0venv\Scripts\pythonw.exe" "%~dp0app.py" 1>>"%LOG%" 2>&1"
    exit /b
)

where pythonw.exe >nul 2>nul
if %errorlevel%==0 (
    start "" cmd /c "pythonw.exe "%~dp0app.py" 1>>"%LOG%" 2>&1"
    exit /b
)

where python.exe >nul 2>nul
if %errorlevel%==0 (
    start "" cmd /c "python.exe "%~dp0app.py" 1>>"%LOG%" 2>&1"
    exit /b
)

echo No Python interpreter found. Install Python 3.10+ and run setup again.>>"%LOG%"
