@echo off
REM Keep Speaker Awake - Launcher
REM Runs the application without showing a console window

cd /d "%~dp0"
start "" venv\Scripts\pythonw.exe app.py
