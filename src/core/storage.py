from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


def make_run_id(image_path: str, query_hint: str | None = None) -> str:
    seed = f"{image_path}|{query_hint or ''}|{datetime.utcnow().isoformat()}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{digest}"


def ensure_run_dirs(base_output_dir: str, run_id: str) -> dict[str, Path]:
    root = Path(base_output_dir) / run_id
    assets = root / "assets"
    reports = root / "reports"
    logs = root / "logs"
    for p in (root, assets, reports, logs):
        p.mkdir(parents=True, exist_ok=True)
    return {"root": root, "assets": assets, "reports": reports, "logs": logs}


def listing_asset_dirs(assets_root: Path, platform: str, item_id: str) -> dict[str, Path]:
    root = assets_root / platform / item_id
    main_images = root / "main_images"
    detail_images = root / "detail_images"
    for p in (root, main_images, detail_images):
        p.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "main_images": main_images,
        "detail_images": detail_images,
    }


def save_run_config(root: Path, config: dict) -> Path:
    path = root / "run_config.json"
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
