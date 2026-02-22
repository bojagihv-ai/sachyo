from pathlib import Path

from src.ui.config_store import load_ui_config, save_ui_config


def test_ui_config_roundtrip(tmp_path: Path):
    p = tmp_path / "ui.json"
    data = {"a": 1, "b": "x"}
    save_ui_config(data, path=p)
    loaded = load_ui_config(path=p)
    assert loaded == data


def test_ui_config_missing_returns_empty(tmp_path: Path):
    p = tmp_path / "missing.json"
    assert load_ui_config(path=p) == {}
