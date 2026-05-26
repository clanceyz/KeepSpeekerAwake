# Keep Speaker Awake

A lightweight Windows background utility that keeps Bluetooth speakers awake by playing inaudible audio, preventing them from entering sleep mode.

## Problem

Bluetooth speakers often go to sleep after a period of silence. When you then play audio (like a word in a dictionary app), the speaker takes time to "wake up", causing you to miss the beginning of the audio.

## Solution

This app periodically plays a short quiet multi-tone burst that:
- Uses normal audible-band frequencies, so Bluetooth codecs and speaker DSPs do not filter it out as silence
- Resets the selected Bluetooth speaker's sleep timer without constant sound
- Uses minimal system resources

The default is a 1.5-second low-frequency burst every 45 seconds at `"volume": 0.01`. If it is too loud, lower `"volume"` in `config.json`. If the speaker still sleeps, either raise the volume gradually or reduce `"interval_seconds"`.

## Installation

1. Ensure Python 3.10+ is installed
2. Run the setup:
   ```powershell
   cd d:\projects\KeepSpeekerAwake
   py -3 -m venv venv
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
  - **Output Device** - Pin the Bluetooth speaker or follow the Windows default output
  - **Exit** - Quit the application

Runtime errors are written to `app.log` next to the script.

### Configuration

The app stores local settings in `config.json`, which is intentionally not committed because it may contain your personal device name. Use `config.example.json` as a starting point if needed.

## Auto-Start with Windows (Optional)

1. Press `Win + R` and type `shell:startup`
2. Create a shortcut to `run.bat` in the Startup folder

## Files

- `app.py` - Main system tray application
- `audio_player.py` - Audio generation and playback module
- `requirements.txt` - Python dependencies
- `run.bat` - Windows launcher (no console)
