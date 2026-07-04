from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rpm_layer.baseline import fit_baseline, score_features
from rpm_layer.detector import attach_predictions, detect_alerts
from rpm_layer.features import extract_features
from rpm_layer.models import AssetProfile
from rpm_layer.monitor import OnlineConditionMonitor, monitor_telemetry
from rpm_layer.simulator import generate_telemetry


PROFILE = AssetProfile(
    asset_id="LIVE-TEST",
    asset_name="Live monitor test axis",
    nominal_speed_rpm=1500.0,
    nominal_current_a=2.8,
    nominal_load_pct=62.0,
    sampling_hz=120.0,
    temperature_warning_c=62.0,
    temperature_critical_c=72.0,
    speed_bands_rpm=(0, 1100, 1350, 1650, 1900, 2500),
)


class OnlineMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.telemetry = generate_telemetry(PROFILE, duration_s=180.0, seed=11)
        cls.features = extract_features(cls.telemetry, sampling_hz=PROFILE.sampling_hz)
        cls.baseline = fit_baseline(cls.features)

    def test_uneven_chunks_match_batch_condition_results(self) -> None:
        expected = score_features(self.features, self.baseline)
        expected_alerts = detect_alerts(expected)
        expected = attach_predictions(expected, expected_alerts)
        result = monitor_telemetry(
            self.telemetry,
            self.baseline,
            sampling_hz=PROFILE.sampling_hz,
            chunk_size=137,
        )
        self.assertEqual(len(result.condition_windows), len(expected))
        self.assertEqual(result.condition_windows["window_start"].tolist(), expected["window_start"].tolist())
        self.assertEqual(result.condition_windows["predicted_diagnosis"].tolist(), expected["predicted_diagnosis"].tolist())
        self.assertEqual(result.samples_ingested, len(self.telemetry))

    def test_duplicate_chunk_boundary_is_rejected(self) -> None:
        monitor = OnlineConditionMonitor(self.baseline, PROFILE.sampling_hz)
        monitor.ingest(self.telemetry.iloc[:100])
        with self.assertRaisesRegex(ValueError, "strictly ordered"):
            monitor.ingest(self.telemetry.iloc[99:150])

    def test_monitor_rejects_unmonitored_window_gaps(self) -> None:
        with self.assertRaisesRegex(ValueError, "unmonitored gaps"):
            OnlineConditionMonitor(self.baseline, PROFILE.sampling_hz, window_s=5.0, step_s=6.0)


if __name__ == "__main__":
    unittest.main()
