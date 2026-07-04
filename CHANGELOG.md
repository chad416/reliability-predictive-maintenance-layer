# Changelog

## 0.5.0 - Streaming and Observability

- Added paced telemetry replay with batched JSONL, InfluxDB, and optional MQTT sinks.
- Added retry/backoff and nanosecond-safe InfluxDB writes for raw telemetry and condition windows.
- Added a SQLite WAL store-and-forward outbox with ordered recovery draining for remote-service outages.
- Added stateful event-time condition monitoring over uneven telemetry chunks with batch-equivalence tests.
- Provisioned a health-checked InfluxDB, Grafana, and Mosquitto stack with a dashboard matching the exported schema.
- Expanded automated coverage for quality failures, line-protocol escaping, replay resource handling, retries, and CLI behavior.
- Upgraded GitHub Actions to current Node 24-compatible major releases.

## 0.4.0 - Portfolio Hardening

- Added telemetry quality gate with timestamp, gap, null, duplicate, and physical range checks.
- Added validation metrics, confusion matrix, detection delay, and fault-recall evidence.
- Added work-order JSON, InfluxDB line protocol, MQTT outbox, and OPC UA node snapshot exports.
- Published the dashboard and evidence artifacts through GitHub Pages.

## 0.1.0 - Initial Project

- Built deterministic telemetry simulation, feature extraction, robust baseline scoring, explainable diagnostics, recommendation generation, dashboard, report, documentation pack, tests, CI, and GitHub Pages deployment.
