from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from rpm_layer.config import write_json, load_json

FEATURE_COLUMNS = [
    "vib_rms_g",
    "vib_peak_to_peak_g",
    "vib_kurtosis",
    "vib_crest_factor",
    "vib_fft_1x_g",
    "vib_fft_2x_g",
    "vib_low_frequency_peak_g",
    "vib_friction_peak_g",
    "vib_broadband_g",
    "current_mean_a",
    "current_std_a",
    "current_load_normalized_a",
    "temperature_mean_c",
    "temperature_slope_c_per_min",
    "acoustic_mean_db",
]


def _iqr(values: pd.Series) -> float:
    q75 = float(values.quantile(0.75))
    q25 = float(values.quantile(0.25))
    return max(q75 - q25, 1e-9)


def fit_baseline(features: pd.DataFrame, healthy_label: str = "healthy") -> dict[str, Any]:
    if features.empty:
        raise ValueError("Cannot fit baseline from an empty feature set.")
    healthy = features[features.get("fault_label_majority", healthy_label) == healthy_label]
    if len(healthy) < 5:
        healthy = features.head(max(5, int(len(features) * 0.2)))

    metrics: dict[str, dict[str, float]] = {}
    for column in FEATURE_COLUMNS:
        if column not in healthy:
            continue
        series = pd.to_numeric(healthy[column], errors="coerce").dropna()
        if series.empty:
            continue
        metrics[column] = {
            "median": round(float(series.median()), 8),
            "iqr": round(_iqr(series), 8),
        }

    return {
        "model_type": "robust_median_iqr",
        "healthy_window_count": int(len(healthy)),
        "feature_count": len(metrics),
        "metrics": metrics,
    }


def score_features(features: pd.DataFrame, baseline: dict[str, Any]) -> pd.DataFrame:
    scored = features.copy()
    metrics = baseline["metrics"]
    positive_scores = []
    for column, stats in metrics.items():
        if column not in scored:
            continue
        median = float(stats["median"])
        iqr = max(float(stats["iqr"]), max(abs(median) * 0.03, 1e-8))
        score_col = f"score_{column}"
        scored[score_col] = (pd.to_numeric(scored[column], errors="coerce") - median) / iqr
        scored[score_col] = scored[score_col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        positive_scores.append(scored[score_col].clip(lower=0.0))

    if positive_scores:
        stacked = np.vstack([series.to_numpy(dtype=float) for series in positive_scores])
        scored["condition_index"] = np.round(np.clip(np.mean(stacked, axis=0) * 12.5, 0.0, 100.0), 2)
    else:
        scored["condition_index"] = 0.0
    return scored


def save_baseline(baseline: dict[str, Any], path: str | Path) -> None:
    write_json(path, baseline)


def load_baseline(path: str | Path) -> dict[str, Any]:
    return load_json(path)
