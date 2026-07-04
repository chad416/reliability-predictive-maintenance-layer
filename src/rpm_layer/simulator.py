from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from rpm_layer.models import AssetProfile


@dataclass(frozen=True)
class FaultSegment:
    start_s: float
    end_s: float
    label: str
    start_severity: float
    end_severity: float

    def severity_at(self, t_s: np.ndarray) -> np.ndarray:
        active = (t_s >= self.start_s) & (t_s < self.end_s)
        if self.end_s <= self.start_s:
            return np.zeros_like(t_s)
        ratio = np.clip((t_s - self.start_s) / (self.end_s - self.start_s), 0.0, 1.0)
        severity = self.start_severity + ratio * (self.end_severity - self.start_severity)
        return np.where(active, severity, 0.0)


def mixed_fault_schedule(duration_s: float) -> list[FaultSegment]:
    """A deterministic FAT-style scenario with recovery gaps between seeded faults."""
    scale = duration_s / 1200.0
    return [
        FaultSegment(240 * scale, 420 * scale, "imbalance", 0.25, 0.9),
        FaultSegment(560 * scale, 760 * scale, "loose_mounting", 0.2, 0.95),
        FaultSegment(830 * scale, 1010 * scale, "belt_tension_drift", 0.25, 0.85),
        FaultSegment(1010 * scale, 1160 * scale, "overheating", 0.25, 1.0),
    ]


def _active_faults(t_s: np.ndarray, schedule: list[FaultSegment]) -> tuple[np.ndarray, np.ndarray]:
    labels = np.full(t_s.shape, "healthy", dtype=object)
    severity = np.zeros_like(t_s, dtype=float)
    for segment in schedule:
        segment_severity = segment.severity_at(t_s)
        active = segment_severity > 0
        labels[active] = segment.label
        severity = np.maximum(severity, segment_severity)
    return labels, severity


def generate_telemetry(
    profile: AssetProfile,
    duration_s: float = 1200.0,
    sampling_hz: float | None = None,
    seed: int = 7,
    start: datetime | None = None,
) -> pd.DataFrame:
    """Generate industrially plausible motor telemetry with seeded maintenance faults."""
    fs = float(sampling_hz or profile.sampling_hz)
    sample_count = int(duration_s * fs)
    t_s = np.arange(sample_count, dtype=float) / fs
    rng = np.random.default_rng(seed)
    start_time = start or datetime(2026, 7, 1, 8, 0, 0)

    schedule = mixed_fault_schedule(duration_s)
    fault_label, fault_severity = _active_faults(t_s, schedule)

    speed_command = profile.nominal_speed_rpm * (
        1.0
        + 0.07 * np.sin(2 * np.pi * t_s / 280.0)
        + 0.04 * np.where((t_s % 360.0) > 220.0, 1.0, -0.3)
    )
    speed_rpm = speed_command + rng.normal(0.0, 5.0, sample_count)
    load_pct = np.clip(
        profile.nominal_load_pct
        + 10.0 * np.sin(2 * np.pi * t_s / 180.0 + 0.7)
        + 4.0 * np.sin(2 * np.pi * t_s / 47.0)
        + rng.normal(0.0, 1.8, sample_count),
        25.0,
        98.0,
    )

    shaft_hz = speed_rpm / 60.0
    phase_1x = 2 * np.pi * np.cumsum(shaft_hz) / fs
    phase_2x = 2 * np.pi * np.cumsum(2.0 * shaft_hz) / fs
    base_amp = 0.018 + 0.00018 * load_pct
    vibration_g = (
        base_amp * np.sin(phase_1x)
        + 0.35 * base_amp * np.sin(phase_2x + 0.4)
        + rng.normal(0.0, 0.012, sample_count)
    )

    current_a = (
        profile.nominal_current_a
        * (0.34 + 0.66 * load_pct / 100.0)
        * (0.94 + 0.06 * speed_rpm / profile.nominal_speed_rpm)
        + rng.normal(0.0, 0.035, sample_count)
    )

    thermal_drive = 0.010 * load_pct + 0.08 * np.maximum(current_a - profile.nominal_current_a, 0.0)
    temperature_c = 31.0 + thermal_drive + 1.2 * np.sin(2 * np.pi * t_s / 900.0)
    acoustic_db = 58.0 + 0.025 * load_pct + rng.normal(0.0, 0.6, sample_count)

    for label in ("imbalance", "loose_mounting", "belt_tension_drift", "overheating"):
        sev = np.where(fault_label == label, fault_severity, 0.0)
        if not np.any(sev):
            continue
        if label == "imbalance":
            vibration_g += sev * (0.085 * np.sin(phase_1x + 0.2))
            vibration_g += sev * rng.normal(0.0, 0.006, sample_count)
            current_a += sev * 0.12
            acoustic_db += sev * 2.0
        elif label == "loose_mounting":
            impacts = (rng.random(sample_count) < (0.006 + 0.03 * sev)).astype(float)
            impact_shape = rng.normal(0.16, 0.04, sample_count) * np.sign(rng.normal(size=sample_count))
            vibration_g += sev * rng.normal(0.0, 0.055, sample_count)
            vibration_g += impacts * impact_shape
            acoustic_db += sev * 5.5 + impacts * 4.0
        elif label == "belt_tension_drift":
            vibration_g += sev * (0.045 * np.sin(2 * np.pi * t_s * 4.0))
            current_a += sev * (0.62 + 0.0045 * load_pct)
            temperature_c += sev * 4.2
            acoustic_db += sev * 2.7
        elif label == "overheating":
            time_in_fault = np.maximum(t_s - np.min(t_s[sev > 0]), 0.0)
            temperature_c += sev * (6.5 + 0.035 * time_in_fault)
            current_a += sev * 0.16
            acoustic_db += sev * 1.1

    timestamps = [start_time + timedelta(seconds=float(value)) for value in t_s]
    return pd.DataFrame(
        {
            "timestamp": [value.isoformat(timespec="microseconds") for value in timestamps],
            "asset_id": profile.asset_id,
            "speed_rpm": np.round(speed_rpm, 3),
            "load_pct": np.round(load_pct, 3),
            "vibration_g": np.round(vibration_g, 6),
            "current_a": np.round(current_a, 5),
            "temperature_c": np.round(temperature_c, 4),
            "acoustic_db": np.round(acoustic_db, 4),
            "fault_label": fault_label,
            "fault_severity": np.round(fault_severity, 4),
        }
    )


def write_telemetry(df: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
