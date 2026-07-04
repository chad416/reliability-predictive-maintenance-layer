from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from rpm_layer.baseline import score_features
from rpm_layer.detector import attach_predictions, detect_alerts
from rpm_layer.features import extract_features


@dataclass(frozen=True)
class MonitorResult:
    condition_windows: pd.DataFrame
    alerts: pd.DataFrame
    samples_ingested: int
    incomplete_samples: int


class OnlineConditionMonitor:
    """Stateful event-time windowing over arbitrarily sized telemetry chunks."""

    def __init__(
        self,
        baseline: dict[str, Any],
        sampling_hz: float,
        window_s: float = 5.0,
        step_s: float = 5.0,
        on_window: Callable[[pd.DataFrame, pd.DataFrame], None] | None = None,
    ) -> None:
        if sampling_hz <= 0:
            raise ValueError("sampling_hz must be positive")
        if window_s <= 0 or step_s <= 0:
            raise ValueError("window_s and step_s must be positive")
        if step_s > window_s:
            raise ValueError("step_s cannot exceed window_s because that would leave unmonitored gaps")
        self.baseline = baseline
        self.sampling_hz = sampling_hz
        self.window_s = window_s
        self.step_s = step_s
        self.on_window = on_window
        self._buffer = pd.DataFrame()
        self._next_window_start: pd.Timestamp | None = None
        self._condition_parts: list[pd.DataFrame] = []
        self._alert_parts: list[pd.DataFrame] = []
        self._samples_ingested = 0
        self._last_timestamp: pd.Timestamp | None = None

    def ingest(self, telemetry_chunk: pd.DataFrame) -> int:
        if telemetry_chunk.empty:
            return 0
        if "timestamp" not in telemetry_chunk:
            raise ValueError("Telemetry chunk must contain a timestamp column.")
        chunk = telemetry_chunk.copy()
        chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], errors="coerce", format="mixed")
        if chunk["timestamp"].isna().any():
            raise ValueError("Telemetry chunk contains invalid timestamps.")
        if not chunk["timestamp"].is_monotonic_increasing:
            raise ValueError("Telemetry chunk timestamps must be monotonic increasing.")
        if self._last_timestamp is not None and chunk["timestamp"].iloc[0] <= self._last_timestamp:
            raise ValueError("Telemetry chunks must be strictly ordered without duplicate timestamps.")

        self._samples_ingested += len(chunk)
        self._last_timestamp = chunk["timestamp"].iloc[-1]
        self._buffer = pd.concat([self._buffer, chunk], ignore_index=True)
        if self._next_window_start is None:
            self._next_window_start = self._buffer["timestamp"].iloc[0]

        produced = 0
        sample_period = pd.Timedelta(seconds=1.0 / self.sampling_hz)
        window_delta = pd.Timedelta(seconds=self.window_s)
        step_delta = pd.Timedelta(seconds=self.step_s)
        while self._next_window_start is not None:
            window_end = self._next_window_start + window_delta
            required_last_sample = window_end - sample_period * 1.5
            if self._buffer["timestamp"].iloc[-1] < required_last_sample:
                break
            mask = (self._buffer["timestamp"] >= self._next_window_start) & (self._buffer["timestamp"] < window_end)
            window = self._buffer.loc[mask]
            minimum_samples = max(4, int(self.window_s * self.sampling_hz * 0.65))
            if len(window) >= minimum_samples:
                features = extract_features(
                    window,
                    sampling_hz=self.sampling_hz,
                    window_s=self.window_s,
                    step_s=self.window_s,
                )
                if not features.empty:
                    scored = score_features(features.head(1), self.baseline)
                    alerts = detect_alerts(scored)
                    scored = attach_predictions(scored, alerts)
                    self._condition_parts.append(scored)
                    if not alerts.empty:
                        self._alert_parts.append(alerts)
                    if self.on_window is not None:
                        self.on_window(scored.copy(), alerts.copy())
                    produced += 1
            self._next_window_start += step_delta
            self._buffer = self._buffer[self._buffer["timestamp"] >= self._next_window_start].reset_index(drop=True)
            if self._buffer.empty:
                break
        return produced

    def result(self) -> MonitorResult:
        conditions = pd.concat(self._condition_parts, ignore_index=True) if self._condition_parts else pd.DataFrame()
        alerts = pd.concat(self._alert_parts, ignore_index=True) if self._alert_parts else pd.DataFrame()
        return MonitorResult(
            condition_windows=conditions,
            alerts=alerts,
            samples_ingested=self._samples_ingested,
            incomplete_samples=len(self._buffer),
        )


def monitor_telemetry(
    telemetry: pd.DataFrame,
    baseline: dict[str, Any],
    sampling_hz: float,
    chunk_size: int = 1000,
    window_s: float = 5.0,
    step_s: float = 5.0,
) -> MonitorResult:
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")
    monitor = OnlineConditionMonitor(baseline, sampling_hz, window_s=window_s, step_s=step_s)
    for start in range(0, len(telemetry), chunk_size):
        monitor.ingest(telemetry.iloc[start : start + chunk_size])
    return monitor.result()
