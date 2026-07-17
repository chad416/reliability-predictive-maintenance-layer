from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from rpm_layer.models import DiagnosticRule, severity_from_score

RULES = {
    "rotor_imbalance": DiagnosticRule(
        diagnosis="rotor_imbalance",
        evidence_fields=("score_vib_fft_1x_g", "score_vib_rms_g", "score_current_mean_a"),
        advisory_score=2.5,
        warning_score=4.5,
        critical_score=7.0,
    ),
    "mechanical_looseness": DiagnosticRule(
        diagnosis="mechanical_looseness",
        evidence_fields=("score_vib_kurtosis", "score_vib_crest_factor", "score_vib_broadband_g"),
        advisory_score=2.8,
        warning_score=4.8,
        critical_score=7.2,
    ),
    "belt_tension_drift": DiagnosticRule(
        diagnosis="belt_tension_drift",
        evidence_fields=("score_current_load_normalized_a", "score_vib_low_frequency_peak_g", "score_temperature_mean_c"),
        advisory_score=1.25,
        warning_score=2.5,
        critical_score=4.5,
    ),
    "elevated_friction": DiagnosticRule(
        diagnosis="elevated_friction",
        evidence_fields=("score_current_load_normalized_a", "score_vib_friction_peak_g", "score_temperature_slope_c_per_min"),
        advisory_score=1.6,
        warning_score=3.5,
        critical_score=6.0,
    ),
    "overheating": DiagnosticRule(
        diagnosis="overheating",
        evidence_fields=("score_temperature_mean_c", "score_temperature_slope_c_per_min", "score_current_mean_a"),
        advisory_score=2.4,
        warning_score=4.2,
        critical_score=6.8,
    ),
    "sensor_or_mounting_issue": DiagnosticRule(
        diagnosis="sensor_or_mounting_issue",
        evidence_fields=("score_vib_crest_factor", "score_vib_broadband_g", "score_current_mean_a"),
        advisory_score=4.5,
        warning_score=6.8,
        critical_score=9.0,
    ),
}


def _value(row: pd.Series, column: str) -> float:
    if column not in row:
        return 0.0
    value = row[column]
    if pd.isna(value):
        return 0.0
    return float(value)


def _positive(row: pd.Series, column: str) -> float:
    return max(_value(row, column), 0.0)


def _diagnostic_scores(row: pd.Series) -> dict[str, float]:
    one_x = _positive(row, "score_vib_fft_1x_g")
    two_x = _positive(row, "score_vib_fft_2x_g")
    vib_rms = _positive(row, "score_vib_rms_g")
    current = _positive(row, "score_current_mean_a")
    current_load = _positive(row, "score_current_load_normalized_a")
    kurtosis = _positive(row, "score_vib_kurtosis")
    crest = _positive(row, "score_vib_crest_factor")
    broadband = _positive(row, "score_vib_broadband_g")
    low_frequency = _positive(row, "score_vib_low_frequency_peak_g")
    friction_peak = _positive(row, "score_vib_friction_peak_g")
    temp = _positive(row, "score_temperature_mean_c")
    temp_slope = _positive(row, "score_temperature_slope_c_per_min")

    imbalance_shape = 1.2 if _value(row, "vib_fft_1x_g") >= _value(row, "vib_fft_2x_g") else 0.85
    sensor_decoupling = max(0.0, broadband + crest - current - temp - 0.50 * vib_rms)

    return {
        "rotor_imbalance": imbalance_shape * (0.58 * one_x + 0.32 * vib_rms + 0.10 * current),
        "mechanical_looseness": 0.25 * kurtosis + 0.25 * crest + 0.35 * broadband + 0.15 * vib_rms,
        "belt_tension_drift": 0.50 * current_load + 0.35 * low_frequency + 0.15 * temp,
        "elevated_friction": 0.40 * current_load + 0.35 * friction_peak + 0.25 * temp_slope,
        "overheating": 0.58 * temp + 0.32 * temp_slope + 0.10 * current,
        "sensor_or_mounting_issue": 0.35 * sensor_decoupling + 0.15 * crest + 0.10 * broadband,
    }


def detect_alerts(scored_features: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str | float]] = []
    for _, row in scored_features.iterrows():
        scores = _diagnostic_scores(row)
        diagnosis, score = max(scores.items(), key=lambda item: item[1])
        rule = RULES[diagnosis]
        severity = severity_from_score(score, rule)
        if severity == "normal":
            continue
        evidence = []
        for field in rule.evidence_fields:
            if field not in row:
                continue
            raw_field = field.removeprefix("score_")
            raw_value = _value(row, raw_field)
            score_value = _value(row, field)
            evidence.append(f"{raw_field}={raw_value:.5g} (robust_score={score_value:.3f})")
        rows.append(
            {
                "window_start": row["window_start"],
                "window_end": row["window_end"],
                "asset_id": row["asset_id"],
                "severity": severity,
                "diagnosis": diagnosis,
                "diagnostic_score": round(float(score), 3),
                "condition_index": round(float(row.get("condition_index", 0.0)), 2),
                "evidence": "; ".join(evidence),
                "validated_fault_label": str(row.get("fault_label_majority", "unknown")),
            }
        )
    return pd.DataFrame(rows)


def attach_predictions(scored_features: pd.DataFrame, alerts: pd.DataFrame) -> pd.DataFrame:
    scored = scored_features.copy()
    scored["predicted_diagnosis"] = "healthy"
    scored["predicted_severity"] = "normal"
    if alerts.empty:
        return scored
    alert_index = alerts.set_index("window_start")
    for idx, row in scored.iterrows():
        key = row["window_start"]
        if key in alert_index.index:
            alert_row = alert_index.loc[key]
            if isinstance(alert_row, pd.DataFrame):
                alert_row = alert_row.sort_values("diagnostic_score", ascending=False).iloc[0]
            scored.at[idx, "predicted_diagnosis"] = alert_row["diagnosis"]
            scored.at[idx, "predicted_severity"] = alert_row["severity"]
    return scored


def aggregate_alerts(alerts: pd.DataFrame) -> pd.DataFrame:
    if alerts.empty:
        return pd.DataFrame(
            columns=[
                "diagnosis",
                "severity",
                "first_seen",
                "last_seen",
                "windows",
                "max_score",
                "max_condition_index",
                "evidence",
            ]
        )
    working = alerts.copy()
    severity_rank = {"advisory": 1, "warning": 2, "critical": 3}
    working["severity_rank"] = working["severity"].map(severity_rank).fillna(0)
    groups = []
    for diagnosis, group in working.groupby("diagnosis", sort=False):
        top = group.sort_values(["severity_rank", "diagnostic_score"], ascending=False).iloc[0]
        groups.append(
            {
                "diagnosis": diagnosis,
                "severity": top["severity"],
                "first_seen": group["window_start"].min(),
                "last_seen": group["window_end"].max(),
                "windows": int(len(group)),
                "max_score": round(float(group["diagnostic_score"].max()), 3),
                "max_condition_index": round(float(group["condition_index"].max()), 2),
                "evidence": top["evidence"],
            }
        )
    return pd.DataFrame(groups).sort_values(["max_condition_index", "max_score"], ascending=False)


def write_alerts(alerts: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    alerts.to_csv(target, index=False)
