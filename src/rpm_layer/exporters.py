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


def build_mqtt_outbox(scored: pd.DataFrame, alerts: pd.DataFrame, recommendations: pd.DataFrame) -> list[dict[str, object]]:
    messages: list[dict[str, object]] = []
    for _, row in scored.tail(60).iterrows():
        messages.append(
            {
                "topic": f"factory/mhc/{row.get('asset_id', 'unknown')}/condition",
                "retain": False,
                "payload": {
                    "timestamp": row.get("window_start", ""),
                    "asset_id": row.get("asset_id", ""),
                    "condition_index": float(row.get("condition_index", 0.0)),
                    "diagnosis": row.get("predicted_diagnosis", "healthy"),
                    "severity": row.get("predicted_severity", "normal"),
                    "vibration_rms_g": float(row.get("vib_rms_g", 0.0)),
                    "current_mean_a": float(row.get("current_mean_a", 0.0)),
                    "temperature_mean_c": float(row.get("temperature_mean_c", 0.0)),
                },
            }
        )
    for _, row in alerts.tail(40).iterrows():
        messages.append(
            {
                "topic": f"factory/mhc/{row.get('asset_id', 'unknown')}/alerts",
                "retain": False,
                "payload": {
                    "timestamp": row.get("window_start", ""),
                    "asset_id": row.get("asset_id", ""),
                    "severity": row.get("severity", ""),
                    "diagnosis": row.get("diagnosis", ""),
                    "condition_index": float(row.get("condition_index", 0.0)),
                    "evidence": row.get("evidence", ""),
                },
            }
        )
    for _, row in recommendations.iterrows():
        messages.append(
            {
                "topic": "factory/mhc/MHC-CONV-AXIS-01/recommendations",
                "retain": True,
                "payload": {
                    "diagnosis": row.get("diagnosis", ""),
                    "priority": row.get("priority", ""),
                    "severity": row.get("severity", ""),
                    "recommended_action": row.get("recommended_action", ""),
                    "verification": row.get("verification", ""),
                },
            }
        )
    return messages


def write_mqtt_outbox(scored: pd.DataFrame, alerts: pd.DataFrame, recommendations: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(message, sort_keys=True) for message in build_mqtt_outbox(scored, alerts, recommendations)]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_opcua_snapshot(scored: pd.DataFrame, alerts: pd.DataFrame, recommendations: pd.DataFrame) -> dict[str, object]:
    latest = scored.iloc[-1].to_dict() if not scored.empty else {}
    latest_alert = alerts.iloc[-1].to_dict() if not alerts.empty else {}
    top_recommendation = recommendations.iloc[0].to_dict() if not recommendations.empty else {}
    timestamp = latest.get("window_start", "")
    asset_id = latest.get("asset_id", "MHC-CONV-AXIS-01")
    return {
        "namespace_uri": "urn:portfolio:reliability-predictive-maintenance",
        "asset_id": asset_id,
        "generated_at": timestamp,
        "nodes": {
            "Assets/MHC-CONV-AXIS-01/Condition/ConditionIndex": {
                "value": float(latest.get("condition_index", 0.0)),
                "unit": "percent",
                "timestamp": timestamp,
            },
            "Assets/MHC-CONV-AXIS-01/Condition/ActiveDiagnosis": {
                "value": latest.get("predicted_diagnosis", "healthy"),
                "timestamp": timestamp,
            },
            "Assets/MHC-CONV-AXIS-01/Condition/ActiveSeverity": {
                "value": latest.get("predicted_severity", "normal"),
                "timestamp": timestamp,
            },
            "Assets/MHC-CONV-AXIS-01/Condition/LastAlertEvidence": {
                "value": latest_alert.get("evidence", ""),
                "timestamp": latest_alert.get("window_start", timestamp),
            },
            "Assets/MHC-CONV-AXIS-01/Maintenance/TopRecommendation": {
                "value": top_recommendation.get("recommended_action", ""),
                "timestamp": top_recommendation.get("first_seen", timestamp),
            },
        },
    }


def write_opcua_snapshot(scored: pd.DataFrame, alerts: pd.DataFrame, recommendations: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_opcua_snapshot(scored, alerts, recommendations), indent=2) + "\n", encoding="utf-8")
