from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _safe_kurtosis(values: np.ndarray) -> float:
    centered = values - np.mean(values)
    std = float(np.std(centered))
    if std < 1e-12:
        return 0.0
    return float(np.mean((centered / std) ** 4))


def _fft_amplitude(values: np.ndarray, fs: float, target_hz: float, bandwidth_hz: float = 0.8) -> float:
    if values.size < 4 or target_hz <= 0:
        return 0.0
    centered = values - np.mean(values)
    freqs = np.fft.rfftfreq(values.size, d=1.0 / fs)
    spectrum = np.abs(np.fft.rfft(centered)) * 2.0 / values.size
    band = (freqs >= max(0.0, target_hz - bandwidth_hz)) & (freqs <= target_hz + bandwidth_hz)
    if not np.any(band):
        return 0.0
    return float(np.max(spectrum[band]))


def _broadband_energy(values: np.ndarray, fs: float, lower_hz: float) -> float:
    if values.size < 4:
        return 0.0
    centered = values - np.mean(values)
    freqs = np.fft.rfftfreq(values.size, d=1.0 / fs)
    spectrum = np.abs(np.fft.rfft(centered)) * 2.0 / values.size
    band = (freqs >= lower_hz) & (freqs <= fs / 2.0)
    if not np.any(band):
        return 0.0
    return float(np.sqrt(np.mean(spectrum[band] ** 2)))


def _majority_label(values: pd.Series) -> str:
    if values.empty:
        return "unknown"
    counts = values.value_counts(dropna=False)
    return str(counts.index[0])


def extract_features(
    telemetry: pd.DataFrame,
    sampling_hz: float,
    window_s: float = 5.0,
    step_s: float = 5.0,
) -> pd.DataFrame:
    """Convert sample-level telemetry into diagnostic windows."""
    if telemetry.empty:
        return pd.DataFrame()

    df = telemetry.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed")
    df = df.sort_values("timestamp").reset_index(drop=True)
    start = df["timestamp"].iloc[0]
    elapsed_s = (df["timestamp"] - start).dt.total_seconds().to_numpy()
    max_t = float(elapsed_s[-1])

    rows: list[dict[str, float | str | int]] = []
    window_start = 0.0
    while window_start + window_s <= max_t + (1.0 / sampling_hz):
        window_end = window_start + window_s
        mask = (elapsed_s >= window_start) & (elapsed_s < window_end)
        window = df.loc[mask]
        if len(window) < max(4, int(window_s * sampling_hz * 0.65)):
            window_start += step_s
            continue

        vib = window["vibration_g"].to_numpy(dtype=float)
        current = window["current_a"].to_numpy(dtype=float)
        temp = window["temperature_c"].to_numpy(dtype=float)
        speed = window["speed_rpm"].to_numpy(dtype=float)
        load = window["load_pct"].to_numpy(dtype=float)
        acoustic = window["acoustic_db"].to_numpy(dtype=float)
        mean_speed = float(np.mean(speed))
        shaft_hz = max(mean_speed / 60.0, 0.1)
        vib_rms = float(np.sqrt(np.mean(vib**2)))
        temp_time_min = np.arange(temp.size, dtype=float) / sampling_hz / 60.0
        temp_slope = float(np.polyfit(temp_time_min, temp, 1)[0]) if temp.size > 2 else 0.0

        rows.append(
            {
                "window_start": window["timestamp"].iloc[0].isoformat(),
                "window_end": window["timestamp"].iloc[-1].isoformat(),
                "asset_id": str(window["asset_id"].iloc[0]),
                "sample_count": int(len(window)),
                "speed_rpm_mean": round(mean_speed, 4),
                "speed_rpm_std": round(float(np.std(speed)), 4),
                "load_pct_mean": round(float(np.mean(load)), 4),
                "vib_rms_g": round(vib_rms, 6),
                "vib_peak_to_peak_g": round(float(np.max(vib) - np.min(vib)), 6),
                "vib_kurtosis": round(_safe_kurtosis(vib), 5),
                "vib_crest_factor": round(float(np.max(np.abs(vib)) / max(vib_rms, 1e-9)), 5),
                "vib_fft_1x_g": round(_fft_amplitude(vib, sampling_hz, shaft_hz), 6),
                "vib_fft_2x_g": round(_fft_amplitude(vib, sampling_hz, 2.0 * shaft_hz), 6),
                "vib_broadband_g": round(_broadband_energy(vib, sampling_hz, lower_hz=min(0.45 * sampling_hz, 4.0 * shaft_hz)), 6),
                "current_mean_a": round(float(np.mean(current)), 5),
                "current_std_a": round(float(np.std(current)), 5),
                "temperature_mean_c": round(float(np.mean(temp)), 4),
                "temperature_slope_c_per_min": round(temp_slope, 5),
                "acoustic_mean_db": round(float(np.mean(acoustic)), 4),
                "fault_label_majority": _majority_label(window["fault_label"]) if "fault_label" in window else "unknown",
                "fault_severity_max": round(float(np.max(window["fault_severity"])) if "fault_severity" in window else 0.0, 4),
            }
        )
        window_start += step_s

    return pd.DataFrame(rows)


def read_telemetry(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_features(features: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(target, index=False)
