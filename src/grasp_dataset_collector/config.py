from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    required_top_keys = ("dataset_root", "dataset_metadata", "camera", "robot", "sample_defaults")
    missing = [key for key in required_top_keys if key not in config]
    if missing:
        raise ValueError(f"配置缺少必需字段: {', '.join(missing)}")

    return config
