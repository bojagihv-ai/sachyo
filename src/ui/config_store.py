from __future__ import annotations

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".sachyo_ui_config.json"


def load_ui_config(path: Path | None = None) -> dict:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_ui_config(data: dict, path: Path | None = None):
    config_path = path or CONFIG_PATH
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
