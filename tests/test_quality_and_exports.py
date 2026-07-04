from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rpm_layer.baseline import fit_baseline
from rpm_layer.exporters import write_influx_line_protocol
from rpm_layer.quality import assess_telemetry_quality


def valid_telemetry() -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=8, freq="10ms")
    return pd.DataFrame(
        {
            "timestamp": timestamps.astype(str),
            "asset_id": "AXIS-01",
            "speed_rpm": 1500.0,
            "load_pct": 60.0,
            "vibration_g": 0.1,
            "current_a": 2.8,
            "temperature_c": 42.0,
            "acoustic_db": 60.0,
        }
    )


class QualityAndExportTests(unittest.TestCase):
    def test_quality_rejects_missing_columns(self) -> None:
        result = assess_telemetry_quality(valid_telemetry().drop(columns=["current_a"]), 100.0)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["missing_columns"], ["current_a"])

    def test_quality_rejects_duplicates_gaps_and_range_violations(self) -> None:
        telemetry = valid_telemetry()
        telemetry.loc[2, "timestamp"] = telemetry.loc[1, "timestamp"]
        telemetry.loc[4, "timestamp"] = "2026-01-01 00:00:01"
        telemetry.loc[5:, "timestamp"] = pd.date_range("2026-01-01 00:00:01.010", periods=3, freq="10ms").astype(str)
        telemetry.loc[3, "temperature_c"] = 140.0
        result = assess_telemetry_quality(telemetry, 100.0)
        self.assertEqual(result["status"], "fail")
        self.assertGreater(result["duplicate_timestamps"], 0)
        self.assertGreater(result["gap_max_ms"], 25.0)
        self.assertEqual(result["range_violations"]["temperature_c"], 1)

    def test_empty_baseline_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            fit_baseline(pd.DataFrame())

    def test_condition_line_protocol_escapes_tags_and_strings(self) -> None:
        scored = pd.DataFrame(
            [{
                "window_start": "2026-01-01T00:00:00",
                "asset_id": "LINE 1,AXIS=A",
                "predicted_diagnosis": "healthy",
                "predicted_severity": "normal",
                "condition_index": 1.25,
                "fault_label_majority": 'operator "check"',
            }]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "condition.lp"
            write_influx_line_protocol(scored, target)
            line = target.read_text(encoding="utf-8")
            self.assertIn("asset_id=LINE\\ 1\\,AXIS\\=A", line)
            self.assertIn('validated_fault_label="operator \\"check\\""', line)
            self.assertTrue(line.endswith("1767225600000000000\n"))

    def test_grafana_dashboard_matches_export_measurement(self) -> None:
        dashboard = json.loads((ROOT / "grafana" / "predictive_maintenance_dashboard.json").read_text(encoding="utf-8"))
        queries = [target["query"] for panel in dashboard["panels"] for target in panel.get("targets", [])]
        self.assertGreaterEqual(len(dashboard["panels"]), 5)
        self.assertTrue(all("condition_window" in query for query in queries))
        self.assertEqual(dashboard["uid"], "rpm-condition-monitoring")


if __name__ == "__main__":
    unittest.main()
