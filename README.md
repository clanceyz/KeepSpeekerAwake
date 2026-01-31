# Keep Speaker Awake

A lightweight Windows background utility that keeps Bluetooth speakers awake by playing inaudible audio, preventing them from entering sleep mode.

## Problem

Bluetooth speakers often go to sleep after a period of silence. When you then play audio (like a word in a dictionary app), the speaker takes time to "wake up", causing you to miss the beginning of the audio.

## Solution

This app continuously plays very quiet white noise (~0.001 volume) that:
- Keeps your Bluetooth speaker in active mode
- Is completely inaudible to human ears
- Uses minimal system resources

## Installation

1. Ensure Python 3.10+ is installed
2. Run the setup:
   ```powershell
   cd d:\projects\KeepSpeekerAwake
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

## Usage

### Quick Start (No Console Window)
Double-click **`run.bat`** to start the app without a console window.

### Manual Start
```powershell
.\venv\Scripts\python.exe app.py
```

### System Tray Controls
- **Green speaker icon** = Audio is playing
- **Gray speaker icon** = Audio is paused
- **Right-click** the icon to:
  - **Pause/Resume** - Toggle audio playback
  - **Exit** - Quit the application

## Auto-Start with Windows (Optional)

1. Press `Win + R` and type `shell:startup`
2. Create a shortcut to `run.bat` in the Startup folder

## Files

- `app.py` - Main system tray application
- `audio_player.py` - Audio generation and playback module
- `requirements.txt` - Python dependencies
- `run.bat` - Windows launcher (no console)
