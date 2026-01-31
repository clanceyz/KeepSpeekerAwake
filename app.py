"""
Keep Speaker Awake - System Tray Application
Prevents Bluetooth speakers from sleeping by playing inaudible audio.
"""

import sys
import threading
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

from audio_player import AudioPlayer


def create_icon_image(color: str = "#4CAF50") -> Image.Image:
    """Create a simple speaker icon for the system tray."""
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw speaker body (rectangle)
    draw.rectangle([12, 20, 28, 44], fill=color)
    
    # Draw speaker cone (triangle)
    draw.polygon([(28, 12), (48, 12), (48, 52), (28, 52)], fill=color)
    
    # Draw sound waves (arcs)
    for i, offset in enumerate([6, 12, 18]):
        alpha = 255 - (i * 50)
        wave_color = (*tuple(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4)), alpha)
        draw.arc([42 + offset, 16, 54 + offset, 48], -60, 60, fill=wave_color, width=3)
    
    return img


class KeepSpeakerAwakeApp:
    """System tray application for keeping speakers awake."""

    def __init__(self):
        self.audio_player = AudioPlayer()
        self.icon = None
        self._setup_tray()

    def _setup_tray(self):
        """Set up the system tray icon and menu."""
        self.icon = pystray.Icon(
            name="KeepSpeakerAwake",
            icon=create_icon_image("#4CAF50"),  # Green = playing
            title="Keep Speaker Awake (Playing)",
            menu=pystray.Menu(
                item(
                    lambda text: "⏸ Pause" if self.audio_player.is_playing else "▶ Resume",
                    self._on_toggle,
                    default=True
                ),
                pystray.Menu.SEPARATOR,
                item("❌ Exit", self._on_exit)
            )
        )

    def _on_toggle(self, icon, item):
        """Handle pause/resume toggle."""
        is_playing = self.audio_player.toggle()
        if is_playing:
            icon.icon = create_icon_image("#4CAF50")  # Green
            icon.title = "Keep Speaker Awake (Playing)"
        else:
            icon.icon = create_icon_image("#9E9E9E")  # Gray
            icon.title = "Keep Speaker Awake (Paused)"
        icon.update_menu()

    def _on_exit(self, icon, item):
        """Handle exit action."""
        self.audio_player.shutdown()
        icon.stop()

    def run(self):
        """Start the application."""
        # Start audio playback
        self.audio_player.start()
        
        # Run the system tray icon (blocks until exit)
        self.icon.run()


def main():
    """Main entry point."""
    app = KeepSpeakerAwakeApp()
    app.run()


if __name__ == "__main__":
    main()
