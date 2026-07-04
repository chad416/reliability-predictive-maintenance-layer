from __future__ import annotations

from pathlib import Path

import pandas as pd


def _markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    if df.empty:
        return "_No rows._"
    view = df.loc[:, [column for column in columns if column in df.columns]]
    if limit is not None:
        view = view.head(limit)
    headers = "| " + " | ".join(view.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        values = [str(row[column]).replace("\n", " ") for column in view.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([headers, divider, *rows])


def _detection_summary(scored: pd.DataFrame) -> pd.DataFrame:
    if "fault_label_majority" not in scored or "predicted_diagnosis" not in scored:
        return pd.DataFrame()
    mapping = {
        "healthy": "healthy",
        "imbalance": "rotor_imbalance",
        "loose_mounting": "mechanical_looseness",
        "belt_tension_drift": "belt_tension_drift",
        "overheating": "overheating",
    }
    rows = []
    for label, expected in mapping.items():
        subset = scored[scored["fault_label_majority"] == label]
        if subset.empty:
            continue
        detected = subset[subset["predicted_diagnosis"] == expected]
        first_detection = detected["window_start"].iloc[0] if not detected.empty else ""
        rows.append(
            {
                "validation_label": label,
                "expected_diagnosis": expected,
                "windows": int(len(subset)),
                "detected_windows": int(len(detected)),
                "first_detection": first_detection,
            }
        )
    return pd.DataFrame(rows)


def write_markdown_report(
    scored_features: pd.DataFrame,
    alerts: pd.DataFrame,
    aggregated_alerts: pd.DataFrame,
    recommendations: pd.DataFrame,
    path: str | Path,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    total_windows = int(len(scored_features))
    alert_windows = int(len(alerts))
    critical_windows = int((alerts["severity"] == "critical").sum()) if not alerts.empty else 0
    max_condition = float(scored_features["condition_index"].max()) if "condition_index" in scored_features else 0.0
    detection = _detection_summary(scored_features)

    report = f"""# Predictive Maintenance Case Report

## Executive Summary

The reliability layer analyzed {total_windows} diagnostic windows and produced {alert_windows} alert windows. The maximum condition index was {max_condition:.1f}/100, with {critical_windows} critical windows. The highest-priority recommendations are listed below and are tied directly to measured vibration, current, and thermal evidence.

This report is designed as FAT-style evidence for a portfolio review: it shows the seeded condition, the features used to detect it, the resulting diagnosis, and the maintenance response.

## Alert Episodes

{_markdown_table(aggregated_alerts, ["diagnosis", "severity", "first_seen", "last_seen", "windows", "max_score", "max_condition_index", "evidence"])}

## Maintenance Action Matrix

{_markdown_table(recommendations, ["priority", "diagnosis", "severity", "downtime_class", "recommended_action", "spares", "verification"])}

## Validation Detection Summary

{_markdown_table(detection, ["validation_label", "expected_diagnosis", "windows", "detected_windows", "first_detection"])}

## Engineering Notes

- The baseline is fitted from healthy windows using robust median/IQR statistics, which is appropriate for commissioning data that may include noise and non-Gaussian process variation.
- The diagnostic layer uses explainable rule scores rather than opaque model output. This is intentional for maintenance acceptance: every alarm must be traceable to evidence an engineer can inspect.
- The current implementation is ready for OPC UA or MQTT acquisition adapters. The CSV data contract is stable and documented in `data/README.md`.
- The system demonstrates safety-oriented and reliability-engineering thinking, but it does not claim certified safety performance or production predictive accuracy without hardware validation.
"""
    target.write_text(report, encoding="utf-8")

