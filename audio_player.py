"""
Audio Player Module
Generates and plays inaudible audio to keep Bluetooth speakers awake.
"""

import numpy as np
import sounddevice as sd
import threading


class AudioPlayer:
    """Plays very quiet white noise to keep audio devices awake."""

    def __init__(self, sample_rate: int = 44100, volume: float = 0.001):
        """
        Initialize the audio player.

        Args:
            sample_rate: Audio sample rate in Hz
            volume: Volume level (0.001 = nearly inaudible)
        """
        self.sample_rate = sample_rate
        self.volume = volume
        self.is_playing = False
        self._stream = None
        self._lock = threading.Lock()

    def _audio_callback(self, outdata, frames, time, status):
        """Generate white noise for the audio stream."""
        if self.is_playing:
            # Generate very quiet white noise
            noise = np.random.uniform(-1, 1, frames) * self.volume
            outdata[:, 0] = noise.astype(np.float32)
        else:
            # Output silence when paused
            outdata.fill(0)

    def start(self):
        """Start playing inaudible audio."""
        with self._lock:
            if self._stream is None:
                self._stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    callback=self._audio_callback,
                    blocksize=1024
                )
                self._stream.start()
            self.is_playing = True

    def stop(self):
        """Stop playing audio (pause)."""
        with self._lock:
            self.is_playing = False

    def resume(self):
        """Resume playing audio."""
        with self._lock:
            self.is_playing = True

    def toggle(self):
        """Toggle between playing and paused states."""
        with self._lock:
            self.is_playing = not self.is_playing
        return self.is_playing

    def shutdown(self):
        """Completely shut down the audio stream."""
        with self._lock:
            self.is_playing = False
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
