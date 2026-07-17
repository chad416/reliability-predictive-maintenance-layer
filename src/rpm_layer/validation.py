from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from rpm_layer.config import write_json

EXPECTED_DIAGNOSIS = {
    "healthy": "healthy",
    "imbalance": "rotor_imbalance",
    "loose_mounting": "mechanical_looseness",
    "belt_tension_drift": "belt_tension_drift",
    "elevated_friction": "elevated_friction",
    "overheating": "overheating",
}


def _timestamp(value: object) -> pd.Timestamp:
    return pd.to_datetime(value)


def validation_summary(scored: pd.DataFrame) -> pd.DataFrame:
    if scored.empty:
        return pd.DataFrame()
    rows = []
    for label, expected in EXPECTED_DIAGNOSIS.items():
        subset = scored[scored["fault_label_majority"] == label]
        if subset.empty:
            continue
        detected = subset[subset["predicted_diagnosis"] == expected]
        fault_start = _timestamp(subset["window_start"].iloc[0])
        first_detection = detected["window_start"].iloc[0] if not detected.empty else ""
        delay_s: float | str = ""
        if first_detection:
            delay_s = round(float((_timestamp(first_detection) - fault_start).total_seconds()), 2)
        rows.append(
            {
                "validation_label": label,
                "expected_diagnosis": expected,
                "windows": int(len(subset)),
                "detected_windows": int(len(detected)),
                "detection_rate_pct": round(100.0 * len(detected) / max(len(subset), 1), 2),
                "first_detection": first_detection,
                "detection_delay_s": delay_s,
            }
        )
    return pd.DataFrame(rows)


def confusion_matrix(scored: pd.DataFrame) -> pd.DataFrame:
    if scored.empty:
        return pd.DataFrame()
    working = scored.copy()
    working["expected_diagnosis"] = working["fault_label_majority"].map(EXPECTED_DIAGNOSIS).fillna("unknown")
    matrix = pd.crosstab(working["expected_diagnosis"], working["predicted_diagnosis"])
    ordered = list(EXPECTED_DIAGNOSIS.values())
    ordered_unique = []
    for value in ordered + list(matrix.columns):
        if value not in ordered_unique:
            ordered_unique.append(value)
    matrix = matrix.reindex(index=ordered_unique, columns=ordered_unique, fill_value=0)
    matrix.index.name = "expected_diagnosis"
    return matrix.reset_index()


def validation_metrics(scored: pd.DataFrame) -> dict[str, Any]:
    if scored.empty:
        return {
            "total_windows": 0,
            "window_accuracy_pct": 0.0,
            "fault_window_recall_pct": 0.0,
            "healthy_false_alert_rate_pct": 0.0,
            "detected_fault_classes": 0,
            "expected_fault_classes": max(len(EXPECTED_DIAGNOSIS) - 1, 0),
        }
    working = scored.copy()
    working["expected_diagnosis"] = working["fault_label_majority"].map(EXPECTED_DIAGNOSIS).fillna("unknown")
    total = len(working)
    correct = int((working["expected_diagnosis"] == working["predicted_diagnosis"]).sum())

    healthy = working[working["expected_diagnosis"] == "healthy"]
    healthy_false = int((healthy["predicted_diagnosis"] != "healthy").sum()) if not healthy.empty else 0

    fault = working[working["expected_diagnosis"] != "healthy"]
    fault_correct = int((fault["expected_diagnosis"] == fault["predicted_diagnosis"]).sum()) if not fault.empty else 0
    expected_faults = {value for key, value in EXPECTED_DIAGNOSIS.items() if key != "healthy"}
    detected_faults = set(fault.loc[fault["expected_diagnosis"] == fault["predicted_diagnosis"], "expected_diagnosis"])

    return {
        "total_windows": int(total),
        "window_accuracy_pct": round(100.0 * correct / max(total, 1), 2),
        "fault_window_recall_pct": round(100.0 * fault_correct / max(len(fault), 1), 2),
        "healthy_false_alert_rate_pct": round(100.0 * healthy_false / max(len(healthy), 1), 2),
        "detected_fault_classes": int(len(detected_faults & expected_faults)),
        "expected_fault_classes": int(len(expected_faults)),
    }


def write_validation_artifacts(scored: pd.DataFrame, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    summary = validation_summary(scored)
    matrix = confusion_matrix(scored)
    metrics = validation_metrics(scored)
    summary.to_csv(target / "validation_summary.csv", index=False)
    matrix.to_csv(target / "confusion_matrix.csv", index=False)
    write_json(target / "validation_metrics.json", metrics)
    return summary, matrix, metrics
