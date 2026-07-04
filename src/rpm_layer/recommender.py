from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from rpm_layer.config import load_maintenance_matrix

SEVERITY_WEIGHT = {"normal": 0, "advisory": 1, "warning": 2, "critical": 3}
PRIORITY_WEIGHT = {"P4": 1, "P3": 2, "P2": 3, "P1": 4}


def build_recommendations(
    aggregated_alerts: pd.DataFrame,
    maintenance_matrix: dict[str, Any] | None = None,
) -> pd.DataFrame:
    matrix = maintenance_matrix or load_maintenance_matrix()
    rows = []
    if aggregated_alerts.empty:
        healthy = matrix["healthy"]
        return pd.DataFrame(
            [
                {
                    "diagnosis": "healthy",
                    "priority": healthy["priority"],
                    "severity": "normal",
                    "first_seen": "",
                    "last_seen": "",
                    "windows": 0,
                    "recommended_action": healthy["recommended_action"],
                    "inspection_steps": " | ".join(healthy["inspection_steps"]),
                    "spares": "",
                    "downtime_class": healthy["downtime_class"],
                    "verification": healthy["verification"],
                    "risk_score": 0,
                }
            ]
        )

    for _, alert in aggregated_alerts.iterrows():
        diagnosis = str(alert["diagnosis"])
        entry = matrix.get(diagnosis, matrix["sensor_or_mounting_issue"])
        severity = str(alert["severity"])
        priority = str(entry["priority"])
        risk_score = (
            SEVERITY_WEIGHT.get(severity, 0) * 10
            + PRIORITY_WEIGHT.get(priority, 0) * 4
            + min(int(alert["windows"]), 12)
        )
        rows.append(
            {
                "diagnosis": diagnosis,
                "priority": priority,
                "severity": severity,
                "first_seen": alert["first_seen"],
                "last_seen": alert["last_seen"],
                "windows": int(alert["windows"]),
                "recommended_action": entry["recommended_action"],
                "inspection_steps": " | ".join(entry["inspection_steps"]),
                "spares": ", ".join(entry["spares"]),
                "downtime_class": entry["downtime_class"],
                "verification": entry["verification"],
                "risk_score": risk_score,
            }
        )
    return pd.DataFrame(rows).sort_values(["risk_score", "priority"], ascending=False)


def write_recommendations(recommendations: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(target, index=False)

