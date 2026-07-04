from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rpm_layer.cli import main
from rpm_layer.spool import SpoolFullError, StoreAndForwardSink, drain_spool
from rpm_layer.streaming import InfluxWriter, JsonlSink, replay_telemetry, telemetry_line_protocol


class RecordingSink:
    def __init__(self) -> None:
        self.batches: list[list[dict[str, object]]] = []
        self.closed = False

    def write(self, records: list[dict[str, object]]) -> None:
        self.batches.append(records.copy())

    def close(self) -> None:
        self.closed = True


class FailingSink:
    def __init__(self) -> None:
        self.closed = False

    def write(self, records: list[dict[str, object]]) -> None:
        raise ConnectionError("historian unavailable")

    def close(self) -> None:
        self.closed = True


def telemetry_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2026-01-01T00:00:00.000000", "asset_id": "AXIS 1", "speed_rpm": 1500.0, "vibration_g": 0.1},
            {"timestamp": "2026-01-01T00:00:00.010000", "asset_id": "AXIS 1", "speed_rpm": 1501.0, "vibration_g": 0.2},
            {"timestamp": "2026-01-01T00:00:00.020000", "asset_id": "AXIS 1", "speed_rpm": 1502.0, "vibration_g": 0.3},
        ]
    )


class StreamingTests(unittest.TestCase):
    def test_line_protocol_has_measurement_tags_fields_and_nanoseconds(self) -> None:
        line = telemetry_line_protocol(telemetry_frame().iloc[0].to_dict())
        self.assertTrue(line.startswith("telemetry,asset_id=AXIS\\ 1 "))
        self.assertIn("speed_rpm=1500.0", line)
        self.assertTrue(line.endswith("1767225600000000000"))

    def test_replay_batches_and_limits_records(self) -> None:
        sink = RecordingSink()
        stats = replay_telemetry(telemetry_frame(), sink, speed=0, batch_size=2, max_records=3)
        self.assertEqual(stats.records_sent, 3)
        self.assertEqual(stats.batches_sent, 2)
        self.assertEqual([len(batch) for batch in sink.batches], [2, 1])
        self.assertTrue(sink.closed)

    def test_replay_closes_sink_when_timestamp_validation_fails(self) -> None:
        sink = RecordingSink()
        bad = telemetry_frame().iloc[::-1].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "monotonic"):
            replay_telemetry(bad, sink, speed=0)
        self.assertTrue(sink.closed)

    def test_jsonl_sink_writes_machine_readable_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "replay" / "telemetry.jsonl"
            stats = replay_telemetry(telemetry_frame(), JsonlSink(target), speed=0, batch_size=2)
            rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(stats.records_sent, 3)
            self.assertEqual(rows[1]["speed_rpm"], 1501.0)

    def test_influx_writer_retries_transient_failures(self) -> None:
        attempts = []

        class Response:
            def close(self) -> None:
                return None

        def opener(outgoing, timeout):
            attempts.append((outgoing, timeout))
            if len(attempts) < 3:
                raise URLError("temporary")
            return Response()

        delays = []
        writer = InfluxWriter("http://localhost:8086", "portfolio", "maintenance", "secret", opener=opener, sleep=delays.append)
        writer.write_lines(["telemetry,asset_id=A speed_rpm=1500.0 1"])
        self.assertEqual(len(attempts), 3)
        self.assertEqual(delays, [0.25, 0.5])
        self.assertEqual(attempts[-1][0].get_header("Authorization"), "Token secret")

    def test_cli_replay_defaults_to_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "input.csv"
            target = Path(temp_dir) / "replay.jsonl"
            telemetry_frame().to_csv(source, index=False)
            result = main(["replay", "--input", str(source), "--jsonl-out", str(target), "--max-records", "2"])
            self.assertEqual(result, 0)
            self.assertEqual(len(target.read_text(encoding="utf-8").splitlines()), 2)

    def test_store_and_forward_retains_then_drains_failed_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            spool_path = Path(temp_dir) / "telemetry.sqlite"
            failing = FailingSink()
            buffered = StoreAndForwardSink(failing, spool_path, retry_interval_s=60.0)
            buffered.write(telemetry_frame().head(2).to_dict(orient="records"))
            buffered.write(telemetry_frame().tail(1).to_dict(orient="records"))
            buffered.close()

            self.assertTrue(failing.closed)
            self.assertEqual(buffered.pending_after_close, 2)

            recovered = RecordingSink()
            delivered, remaining = drain_spool(spool_path, recovered)
            self.assertEqual(delivered, 3)
            self.assertEqual(remaining, 0)
            self.assertEqual([len(batch) for batch in recovered.batches], [2, 1])
            self.assertTrue(recovered.closed)

    def test_store_and_forward_applies_bounded_backpressure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            buffered = StoreAndForwardSink(
                FailingSink(),
                Path(temp_dir) / "telemetry.sqlite",
                retry_interval_s=60.0,
                max_batches=1,
            )
            buffered.write(telemetry_frame().head(1).to_dict(orient="records"))
            with self.assertRaisesRegex(SpoolFullError, "capacity"):
                buffered.write(telemetry_frame().tail(1).to_dict(orient="records"))
            buffered.close()


if __name__ == "__main__":
    unittest.main()
