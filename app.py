"""
Keep Speaker Awake - System Tray Application
Prevents Bluetooth speakers from sleeping by playing inaudible audio.
"""

import logging
import threading
from functools import partial
from pathlib import Path

import pystray
import sounddevice as sd
from PIL import Image, ImageDraw
from pystray import MenuItem as item

import config
from audio_player import AudioPlayer

POLL_INTERVAL_SEC = 2.0
LOG_PATH = Path(__file__).resolve().parent / "app.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def create_icon_image(color: str = "#4CAF50") -> Image.Image:
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([12, 20, 28, 44], fill=color)
    draw.polygon([(28, 12), (48, 12), (48, 52), (28, 52)], fill=color)
    for i, offset in enumerate([6, 12, 18]):
        alpha = 255 - (i * 50)
        wave_color = (*tuple(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4)), alpha)
        draw.arc([42 + offset, 16, 54 + offset, 48], -60, 60, fill=wave_color, width=3)
    return img


def _output_devices() -> list[tuple[int, str]]:
    """WASAPI output devices (matches what Windows Settings shows)."""
    hostapis = sd.query_hostapis()
    return [
        (i, d['name'])
        for i, d in enumerate(sd.query_devices())
        if d['max_output_channels'] > 0
        and hostapis[d['hostapi']]['name'] == 'Windows WASAPI'
    ]


def _default_output_index() -> int | None:
    try:
        d = sd.default.device[1]
        return d if isinstance(d, int) and d >= 0 else None
    except Exception:
        return None


def _find_device_by_name(name: str) -> int | None:
    for idx, n in _output_devices():
        if n == name:
            return idx
    return None


class KeepSpeakerAwakeApp:
    def __init__(self):
        cfg = config.load()
        # cfg["device_name"] is None / missing → auto-follow system default.
        self._target_name: str | None = cfg.get("device_name")
        self._audio_settings = {
            "volume": float(cfg.get("volume", 0.01)),
            "frequencies": tuple(cfg.get("frequencies", [180.0, 240.0, 320.0])),
            "burst_seconds": float(cfg.get("burst_seconds", 1.5)),
            "interval_seconds": float(cfg.get("interval_seconds", 45.0)),
        }
        self._current_device_idx: int | None = None
        self.audio_player: AudioPlayer | None = None
        self._stop_poll = threading.Event()
        self._stream_lock = threading.RLock()

        self.icon = pystray.Icon(
            name="KeepSpeakerAwake",
            icon=create_icon_image("#4CAF50"),
            title="Keep Speaker Awake",
            menu=pystray.Menu(
                item(
                    lambda _i: "Pause" if self._is_playing() else "Resume",
                    self._on_toggle,
                    default=True,
                ),
                item("Output Device", pystray.Menu(self._device_menu_items)),
                pystray.Menu.SEPARATOR,
                item("Exit", self._on_exit),
            ),
        )

    # ---- audio lifecycle ----

    def _is_playing(self) -> bool:
        return self.audio_player is not None and self.audio_player.is_playing

    def _resolve_target_index(self) -> int | None:
        if self._target_name is None:
            return _default_output_index()
        return _find_device_by_name(self._target_name)

    def _ensure_stream_on(self, device_idx: int | None, was_playing: bool = True) -> None:
        """Switch the active stream to device_idx (or system default if None)."""
        with self._stream_lock:
            if self._target_name is not None and device_idx is None:
                self._shutdown_stream()
                self._refresh_title(status="Pinned device not connected")
                return

            if device_idx == self._current_device_idx and self.audio_player is not None:
                if was_playing and not self.audio_player.is_playing:
                    self.audio_player.resume()
                return

            old = self.audio_player
            try:
                new_player = AudioPlayer(device=device_idx, **self._audio_settings)
                new_player.start()
                if not was_playing:
                    new_player.stop()
            except Exception:
                logging.exception("Failed to start audio stream for device %r", device_idx)
                self.icon.title = "Keep Speaker Awake (device error - see app.log)"
                return

            self.audio_player = new_player
            self._current_device_idx = device_idx
            if old is not None:
                old.shutdown()
            logging.info(
                "Audio stream started: device=%r sample_rate=%s channels=%s volume=%s frequencies=%s burst_seconds=%s interval_seconds=%s",
                device_idx,
                new_player.sample_rate,
                new_player._channels,
                new_player.volume,
                new_player.frequencies,
                new_player.burst_seconds,
                new_player.interval_seconds,
            )
            self._refresh_title()

    def _shutdown_stream(self) -> None:
        if self.audio_player is not None:
            self.audio_player.shutdown()
            self.audio_player = None
        self._current_device_idx = None

    def _refresh_title(self, status: str | None = None) -> None:
        mode = "auto" if self._target_name is None else "pinned"
        if status:
            self.icon.title = f"Keep Speaker Awake ({mode}, {status})"
            return
        if self._current_device_idx is None:
            self.icon.title = f"Keep Speaker Awake ({mode}, no device)"
            return
        try:
            name = sd.query_devices(self._current_device_idx)['name']
        except Exception:
            name = f"#{self._current_device_idx}"
        state = "Playing" if self._is_playing() else "Paused"
        self.icon.title = f"Keep Speaker Awake - {name} [{mode}, {state}]"

    # ---- background poll: follow system default ----

    def _poll_loop(self) -> None:
        while not self._stop_poll.wait(POLL_INTERVAL_SEC):
            try:
                target = self._resolve_target_index()
                if target != self._current_device_idx:
                    self._ensure_stream_on(target, was_playing=self._is_playing())
            except Exception:
                logging.exception("Device poll failed")

    # ---- menu handlers ----

    def _device_menu_items(self):
        # "Auto (follow system default)" entry
        auto_prefix = "* " if self._target_name is None else "   "
        yield item(f"{auto_prefix}Auto (follow system default)", partial(self._on_select_device, None))
        yield pystray.Menu.SEPARATOR
        for idx, name in _output_devices():
            prefix = "* " if name == self._target_name else "   "
            yield item(f"{prefix}{name}", partial(self._on_select_device, name))

    def _on_select_device(self, target_name: str | None, icon, menu_item):
        """target_name=None → auto-follow system; otherwise pin by name."""
        self._target_name = target_name
        config.save({
            "device_name": target_name,
            "volume": self._audio_settings["volume"],
            "frequencies": list(self._audio_settings["frequencies"]),
            "burst_seconds": self._audio_settings["burst_seconds"],
            "interval_seconds": self._audio_settings["interval_seconds"],
        })
        new_idx = self._resolve_target_index()
        self._ensure_stream_on(new_idx, was_playing=self._is_playing())
        icon.update_menu()

    def _on_toggle(self, icon, menu_item):
        if self.audio_player is None:
            return
        if self.audio_player.toggle():
            icon.icon = create_icon_image("#4CAF50")
        else:
            icon.icon = create_icon_image("#9E9E9E")
        self._refresh_title()
        icon.update_menu()

    def _on_exit(self, icon, menu_item):
        self._stop_poll.set()
        with self._stream_lock:
            self._shutdown_stream()
        icon.stop()

    # ---- entry ----

    def run(self):
        logging.info("Keep Speaker Awake starting")
        self._ensure_stream_on(self._resolve_target_index(), was_playing=True)
        threading.Thread(target=self._poll_loop, daemon=True).start()
        self.icon.run()


def main():
    KeepSpeakerAwakeApp().run()


if __name__ == "__main__":
    main()
