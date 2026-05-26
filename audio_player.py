"""
Audio Player Module
Generates periodic, codec-visible keep-awake audio bursts.
"""

import math
import threading

import numpy as np
import sounddevice as sd


class AudioPlayer:
    """Plays periodic quiet multi-tone bursts to keep audio devices awake."""

    def __init__(
        self,
        sample_rate: int | None = None,
        volume: float = 0.01,
        frequencies: tuple[float, ...] = (180.0, 240.0, 320.0),
        burst_seconds: float = 1.5,
        interval_seconds: float = 45.0,
        device: int | None = None,
        blocksize: int = 2048,
    ):
        self.volume = volume
        self.frequencies = frequencies
        self.burst_seconds = burst_seconds
        self.interval_seconds = interval_seconds
        self.device = device
        self.blocksize = blocksize
        self.is_playing = False
        self._stream = None
        self._lock = threading.Lock()
        self._sample_rate = sample_rate or self._detect_sample_rate()
        self._channels = self._detect_channels()
        self._phases = np.zeros(len(self.frequencies), dtype=np.float64)
        self._phase_incs = (
            2.0 * math.pi * np.array(self.frequencies, dtype=np.float64) / self._sample_rate
        )
        self._sample_cursor = 0

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def _detect_sample_rate(self) -> int:
        try:
            info = sd.query_devices(self.device, 'output')
            return int(info['default_samplerate'])
        except Exception:
            return 48000

    def _detect_channels(self) -> int:
        """Return the channel count of the target device (default to stereo)."""
        try:
            info = sd.query_devices(self.device, 'output')
            return min(info['max_output_channels'], 2)
        except Exception:
            return 2

    def _audio_callback(self, outdata, frames, _time, status):
        if status:
            print(f"Audio stream status: {status}", flush=True)

        if self.is_playing:
            offsets = np.arange(frames, dtype=np.float64)
            burst_frames = max(1, int(self.burst_seconds * self._sample_rate))
            interval_frames = max(burst_frames, int(self.interval_seconds * self._sample_rate))
            positions = (self._sample_cursor + offsets.astype(np.int64)) % interval_frames
            active = positions < burst_frames

            if not np.any(active):
                outdata.fill(0)
                self._sample_cursor += frames
                return

            phases = self._phases[:, None] + self._phase_incs[:, None] * offsets
            wave = np.sin(phases).sum(axis=0)
            wave *= self.volume / len(self.frequencies)

            fade_frames = min(int(0.03 * self._sample_rate), burst_frames // 2)
            if fade_frames > 0:
                envelope = np.ones(frames, dtype=np.float64)
                envelope = np.minimum(envelope, positions / fade_frames)
                envelope = np.minimum(envelope, (burst_frames - positions) / fade_frames)
                envelope = np.clip(envelope, 0.0, 1.0)
                wave *= envelope

            wave[~active] = 0.0
            wave = wave.astype(np.float32)
            outdata[:] = wave[:, None]
            self._phases = (self._phases + self._phase_incs * frames) % (2.0 * math.pi)
            self._sample_cursor += frames
        else:
            outdata.fill(0)

    def start(self):
        """Start playing inaudible audio."""
        with self._lock:
            if self._stream is None:
                self._stream = sd.OutputStream(
                    samplerate=self._sample_rate,
                    channels=self._channels,
                    dtype=np.float32,
                    callback=self._audio_callback,
                    blocksize=self.blocksize,
                    device=self.device,
                    latency='high',
                )
            self.is_playing = True
            if not self._stream.active:
                self._stream.start()

    def stop(self):
        """Stop playing audio (pause)."""
        with self._lock:
            self.is_playing = False
            if self._stream and self._stream.active:
                self._stream.stop()

    def resume(self):
        """Resume playing audio."""
        self.start()

    def toggle(self):
        """Toggle between playing and paused states."""
        with self._lock:
            should_play = not self.is_playing
        if should_play:
            self.start()
        else:
            self.stop()
        return should_play

    def shutdown(self):
        """Completely shut down the audio stream."""
        with self._lock:
            self.is_playing = False
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
