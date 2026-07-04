from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rpm_layer.baseline import fit_baseline, score_features
from rpm_layer.detector import aggregate_alerts, attach_predictions, detect_alerts
from rpm_layer.features import extract_features
from rpm_layer.models import AssetProfile
from rpm_layer.recommender import build_recommendations
from rpm_layer.simulator import generate_telemetry


PROFILE = AssetProfile(
    asset_id="TEST-ASSET",
    asset_name="Test conveyor axis",
    nominal_speed_rpm=1500.0,
    nominal_current_a=2.8,
    nominal_load_pct=62.0,
    sampling_hz=120.0,
    temperature_warning_c=62.0,
    temperature_critical_c=72.0,
    speed_bands_rpm=(0, 1100, 1350, 1650, 1900, 2500),
)


class PipelineTests(unittest.TestCase):
    def test_simulator_outputs_expected_columns(self) -> None:
        telemetry = generate_telemetry(PROFILE, duration_s=180.0, seed=3)
        self.assertGreater(len(telemetry), 1000)
        for column in ["timestamp", "speed_rpm", "vibration_g", "current_a", "temperature_c", "fault_label"]:
            self.assertIn(column, telemetry.columns)
        self.assertIn("imbalance", set(telemetry["fault_label"]))

    def test_features_and_detection_produce_maintenance_recommendations(self) -> None:
        telemetry = generate_telemetry(PROFILE, duration_s=1200.0, seed=5)
        features = extract_features(telemetry, sampling_hz=PROFILE.sampling_hz)
        baseline = fit_baseline(features)
        scored = score_features(features, baseline)
        alerts = detect_alerts(scored)
        scored = attach_predictions(scored, alerts)
        episodes = aggregate_alerts(alerts)
        recommendations = build_recommendations(episodes)

        self.assertFalse(features.empty)
        self.assertIn("condition_index", scored.columns)
        self.assertGreater(scored["condition_index"].max(), 10.0)
        expected = {"rotor_imbalance", "mechanical_looseness", "belt_tension_drift", "overheating"}
        self.assertFalse(alerts.empty)
        self.assertFalse(recommendations.empty)
        self.assertTrue(expected.issubset(set(recommendations["diagnosis"])))


if __name__ == "__main__":
    unittest.main()
