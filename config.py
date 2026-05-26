"""Persistent app config stored next to the script."""

import json
import os
from pathlib import Path

_PATH = Path(__file__).resolve().parent / "config.json"


def load() -> dict:
    try:
        return json.loads(_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(data: dict) -> None:
    tmp_path = _PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp_path, _PATH)
