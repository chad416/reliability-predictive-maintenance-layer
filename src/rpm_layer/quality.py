from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from rpm_layer.config import write_json

REQUIRED_COLUMNS = [
    "timestamp",
    "asset_id",
    "speed_rpm",
    "load_pct",
    "vibration_g",
    "current_a",
    "temperature_c",
    "acoustic_db",
]


def assess_telemetry_quality(telemetry: pd.DataFrame, expected_sampling_hz: float) -> dict[str, Any]:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in telemetry.columns]
    metrics: dict[str, Any] = {
        "status": "pass",
        "sample_count": int(len(telemetry)),
        "expected_sampling_hz": float(expected_sampling_hz),
        "missing_columns": missing_columns,
        "null_counts": {},
        "duplicate_timestamps": 0,
        "monotonic_timestamps": True,
        "estimated_sampling_hz": 0.0,
        "gap_p95_ms": 0.0,
        "gap_max_ms": 0.0,
        "range_violations": {},
    }
    if telemetry.empty or missing_columns:
        metrics["status"] = "fail"
        return metrics

    df = telemetry.copy()
    metrics["null_counts"] = {column: int(df[column].isna().sum()) for column in REQUIRED_COLUMNS}
    timestamps = pd.to_datetime(df["timestamp"], errors="coerce", format="mixed")
    if timestamps.isna().any():
        metrics["status"] = "fail"
        metrics["timestamp_parse_failures"] = int(timestamps.isna().sum())
        return metrics

    metrics["duplicate_timestamps"] = int(timestamps.duplicated().sum())
    metrics["monotonic_timestamps"] = bool(timestamps.is_monotonic_increasing)
    gaps_ms = timestamps.sort_values().diff().dropna().dt.total_seconds() * 1000.0
    if not gaps_ms.empty:
        median_gap_ms = float(gaps_ms.median())
        metrics["estimated_sampling_hz"] = round(1000.0 / median_gap_ms, 4) if median_gap_ms > 0 else 0.0
        metrics["gap_p95_ms"] = round(float(gaps_ms.quantile(0.95)), 4)
        metrics["gap_max_ms"] = round(float(gaps_ms.max()), 4)

    ranges = {
        "speed_rpm": (0.0, 3000.0),
        "load_pct": (0.0, 110.0),
        "vibration_g": (-5.0, 5.0),
        "current_a": (0.0, 20.0),
        "temperature_c": (-20.0, 120.0),
        "acoustic_db": (20.0, 120.0),
    }
    violations = {}
    for column, (lower, upper) in ranges.items():
        series = pd.to_numeric(df[column], errors="coerce")
        violations[column] = int(((series < lower) | (series > upper) | series.isna()).sum())
    metrics["range_violations"] = violations

    expected_gap_ms = 1000.0 / expected_sampling_hz if expected_sampling_hz > 0 else 0.0
    has_nulls = any(count > 0 for count in metrics["null_counts"].values())
    has_range_violations = any(count > 0 for count in violations.values())
    has_gap_problem = expected_gap_ms > 0 and metrics["gap_max_ms"] > expected_gap_ms * 2.5
    if has_nulls or has_range_violations or metrics["duplicate_timestamps"] > 0 or not metrics["monotonic_timestamps"] or has_gap_problem:
        metrics["status"] = "fail"
    return metrics


def write_quality_report(telemetry: pd.DataFrame, expected_sampling_hz: float, path: str | Path) -> dict[str, Any]:
    metrics = assess_telemetry_quality(telemetry, expected_sampling_hz)
    write_json(path, metrics)
    return metrics
