# Traceability Matrix

| Requirement | Evidence artifact | Implementation |
| --- | --- | --- |
| Monitor motor vibration, current, temperature, speed, and load | `data/README.md`, `output/demo/features.csv` | `src/rpm_layer/features.py` |
| Detect rotor imbalance using explainable evidence | `output/demo/alert_episodes.csv`, report alert table | `src/rpm_layer/detector.py` |
| Detect mechanical looseness using impact/broadband evidence | `output/demo/alert_episodes.csv`, FMEA worksheet | `src/rpm_layer/detector.py`, `docs/fmea.md` |
| Detect belt tension drift with current-led symptoms | `output/demo/validation_summary.csv` | `src/rpm_layer/simulator.py`, `src/rpm_layer/detector.py` |
| Detect overheating with thermal level and slope | `output/demo/alert_episodes.csv` | `src/rpm_layer/detector.py` |
| Keep healthy operation free from nuisance alerts | `output/demo/validation_metrics.json` | `src/rpm_layer/validation.py` |
| Prove telemetry is usable before analytics | `output/demo/data_quality.json` | `src/rpm_layer/quality.py` |
| Produce maintenance actions, spares, and verification criteria | `output/demo/recommendations.csv`, `output/demo/work_orders.json` | `src/rpm_layer/recommender.py`, `src/rpm_layer/exporters.py` |
| Provide operations dashboard | `dashboard/index.html`, GitHub Pages site | `src/rpm_layer/dashboard.py` |
| Demonstrate OT/IT integration contracts | `output/demo/mqtt_outbox.jsonl`, `output/demo/opcua_snapshot.json`, `output/demo/condition_windows.lp` | `src/rpm_layer/exporters.py` |
| Replay timestamped telemetry to edge services | `output/demo/telemetry_replay.jsonl`, replay smoke test | `src/rpm_layer/streaming.py`, `src/rpm_layer/cli.py` |
| Prevent telemetry loss during service outages | Durable SQLite outbox and recovery tests | `src/rpm_layer/spool.py`, `tests/test_streaming.py` |
| Analyze condition windows as telemetry arrives | Live monitor summary and batch-equivalence tests | `src/rpm_layer/monitor.py`, `tests/test_monitor.py` |
| Deploy historian, broker, and live dashboard | Provisioned Docker Compose stack and Grafana dashboard | `docker-compose.yml`, `grafana/provisioning/`, `deploy/mosquitto.conf` |
| Provide RAM/FMEA-style engineering documentation | `docs/fmea.md`, `docs/fault_tree.md`, `docs/maintenance_strategy.md` | Documentation pack |
| Provide CI-verifiable reproducibility | GitHub Actions CI run | `.github/workflows/ci.yml` |

## Acceptance Evidence

The demo scenario intentionally includes normal operation and four seeded faults: rotor imbalance, mechanical looseness, belt tension drift, and overheating. The validation artifacts report detection counts, detection delay, confusion matrix, window accuracy, fault-window recall, and healthy false-alert rate.
