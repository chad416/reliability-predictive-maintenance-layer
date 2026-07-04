# Evidence Pack

The project generates a complete review pack with `python scripts/run_demo.py`.

| Artifact | Purpose |
| --- | --- |
| `dashboard/index.html` | Self-contained dashboard for portfolio review |
| `reports/maintenance_case_report.md` | Engineering case report with alerts, recommendations, validation, and confusion matrix |
| `output/demo/scored_features.csv` | Feature windows with scores and predicted diagnoses |
| `output/demo/alert_episodes.csv` | Aggregated diagnostic episodes |
| `output/demo/recommendations.csv` | Maintenance action matrix |
| `output/demo/work_orders.json` | Work-order-shaped maintenance handoff |
| `output/demo/validation_summary.csv` | Detection count and delay by seeded condition |
| `output/demo/confusion_matrix.csv` | Expected-versus-predicted diagnostic matrix |
| `output/demo/validation_metrics.json` | Portfolio-ready validation KPIs |
| `output/demo/data_quality.json` | Telemetry integrity gate for timestamps, gaps, nulls, duplicates, and physical ranges |
| `output/demo/condition_windows.lp` | InfluxDB line protocol for time-series ingestion |
| `output/demo/mqtt_outbox.jsonl` | MQTT-style condition, alert, and recommendation messages |
| `output/demo/opcua_snapshot.json` | OPC UA-facing node snapshot for supervisory integration |
| `output/demo/telemetry_replay.jsonl` | CI smoke evidence from the paced acquisition replay path |
| `output/live/live_monitor_summary.json` | Stateful chunk-processing counts and incomplete-buffer evidence |
| `output/live/live_alerts.csv` | Alerts emitted as event-time windows close |
| `output/live/live_condition_windows.lp` | Online condition windows ready for historian ingestion |

The raw telemetry file is intentionally ignored because it is reproducible and large. Reviewers should regenerate it instead of versioning it.
