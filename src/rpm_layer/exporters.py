from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _safe_tag(value: object) -> str:
    return str(value).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def _safe_field_string(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def write_influx_line_protocol(scored: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for _, row in scored.iterrows():
        timestamp_ns = int(pd.Timestamp(row["window_start"]).timestamp() * 1_000_000_000)
        tags = (
            f"asset_id={_safe_tag(row.get('asset_id', 'unknown'))},"
            f"diagnosis={_safe_tag(row.get('predicted_diagnosis', 'unknown'))},"
            f"severity={_safe_tag(row.get('predicted_severity', 'normal'))}"
        )
        fields = [
            f"condition_index={float(row.get('condition_index', 0.0))}",
            f"vib_rms_g={float(row.get('vib_rms_g', 0.0))}",
            f"vib_fft_1x_g={float(row.get('vib_fft_1x_g', 0.0))}",
            f"current_mean_a={float(row.get('current_mean_a', 0.0))}",
            f"temperature_mean_c={float(row.get('temperature_mean_c', 0.0))}",
            f"validated_fault_label=\"{_safe_field_string(row.get('fault_label_majority', 'unknown'))}\"",
        ]
        lines.append(f"condition_window,{tags} {','.join(fields)} {timestamp_ns}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_work_orders(recommendations: pd.DataFrame) -> list[dict[str, object]]:
    work_orders = []
    for idx, row in recommendations.reset_index(drop=True).iterrows():
        diagnosis = str(row["diagnosis"])
        created = str(row.get("first_seen", "")) or "demo-generated"
        work_orders.append(
            {
                "work_order_id": f"RPM-{idx + 1:04d}-{diagnosis.upper().replace('_', '-')}",
                "asset_id": "MHC-CONV-AXIS-01",
                "source": "predictive_maintenance_layer",
                "created_from": created,
                "priority": row.get("priority", ""),
                "severity": row.get("severity", ""),
                "diagnosis": diagnosis,
                "downtime_class": row.get("downtime_class", ""),
                "recommended_action": row.get("recommended_action", ""),
                "inspection_steps": str(row.get("inspection_steps", "")).split(" | "),
                "spares": [item.strip() for item in str(row.get("spares", "")).split(",") if item.strip()],
                "verification": row.get("verification", ""),
                "status": "ready_for_maintenance_review",
            }
        )
    return work_orders


def write_work_orders(recommendations: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_work_orders(recommendations), indent=2) + "\n", encoding="utf-8")

