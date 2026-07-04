from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AssetProfile:
    asset_id: str
    asset_name: str
    nominal_speed_rpm: float
    nominal_current_a: float
    nominal_load_pct: float
    sampling_hz: float
    temperature_warning_c: float
    temperature_critical_c: float
    speed_bands_rpm: tuple[float, ...]

    @classmethod
    def from_mapping(cls, payload: dict) -> "AssetProfile":
        return cls(
            asset_id=str(payload["asset_id"]),
            asset_name=str(payload["asset_name"]),
            nominal_speed_rpm=float(payload["nominal_speed_rpm"]),
            nominal_current_a=float(payload["nominal_current_a"]),
            nominal_load_pct=float(payload["nominal_load_pct"]),
            sampling_hz=float(payload["sampling_hz"]),
            temperature_warning_c=float(payload["temperature_warning_c"]),
            temperature_critical_c=float(payload["temperature_critical_c"]),
            speed_bands_rpm=tuple(float(value) for value in payload["speed_bands_rpm"]),
        )


@dataclass(frozen=True)
class BaselineMetric:
    median: float
    iqr: float

    def robust_score(self, value: float) -> float:
        scale = self.iqr if self.iqr > 1e-9 else max(abs(self.median) * 0.05, 1e-6)
        return (value - self.median) / scale


@dataclass(frozen=True)
class DiagnosticRule:
    diagnosis: str
    evidence_fields: tuple[str, ...]
    advisory_score: float
    warning_score: float
    critical_score: float


def severity_from_score(score: float, rule: DiagnosticRule) -> str:
    if score >= rule.critical_score:
        return "critical"
    if score >= rule.warning_score:
        return "warning"
    if score >= rule.advisory_score:
        return "advisory"
    return "normal"


def first_present(candidates: Iterable[str], row: dict) -> str:
    for candidate in candidates:
        value = row.get(candidate)
        if value not in (None, ""):
            return str(value)
    return ""

