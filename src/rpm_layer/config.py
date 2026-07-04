from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = PROJECT_ROOT / "config" / "asset_profile.json"
DEFAULT_MAINTENANCE_MATRIX = PROJECT_ROOT / "config" / "maintenance_matrix.json"


def load_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_asset_profile(path: str | Path = DEFAULT_PROFILE) -> dict[str, Any]:
    return load_json(path)


def load_maintenance_matrix(path: str | Path = DEFAULT_MAINTENANCE_MATRIX) -> dict[str, Any]:
    return load_json(path)

