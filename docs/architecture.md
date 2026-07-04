# Architecture

## Purpose

The reliability layer sits above the industrial control layer. It does not own motion control, safety interlocks, or machine sequencing. It observes telemetry, turns samples into condition features, scores those features against a commissioned baseline, and produces maintenance actions that can be reviewed by engineering and operations.

## Logical Flow

```mermaid
flowchart LR
  Sensors["Vibration, current, temperature, speed, load"] --> Acquisition["Acquisition and paced replay adapter"]
  Acquisition --> Feature["Rolling feature extraction"]
  Feature --> Baseline["Robust healthy baseline"]
  Baseline --> Diagnostics["Explainable diagnostic rules"]
  Diagnostics --> Alerts["Alarm and event records"]
  Alerts --> Maint["Maintenance recommendation matrix"]
  Alerts --> Dashboard["Dashboard and case report"]
  Acquisition --> MQTT["MQTT edge broker"]
  Acquisition --> Historian["InfluxDB historian"]
  Historian --> Grafana["Provisioned Grafana dashboard"]
```

## Package Boundaries

- `simulator.py` creates deterministic commissioning and seeded-fault data before hardware is available.
- `features.py` is the signal-processing layer. It computes RMS, kurtosis, crest factor, FFT 1x/2x amplitudes, broadband vibration, current statistics, and temperature slope.
- `baseline.py` fits robust healthy behavior using median/IQR statistics.
- `detector.py` maps evidence to explainable diagnostic scores and alert severities.
- `recommender.py` converts alert episodes into maintenance actions, spares, downtime class, and verification criteria.
- `reporting.py` and `dashboard.py` create the public engineering evidence.
- `streaming.py` replays acquisition samples with bounded batching and publishes to JSONL, InfluxDB, or MQTT sinks.

## Integration Boundary

CSV remains the deterministic acquisition boundary because it is easy to validate and version. The replay adapter can now deliver that contract to InfluxDB and MQTT; a field adapter should subscribe to:

- OPC UA nodes from PLC, drive, or SCADA.
- MQTT topics from an edge gateway.
- Local DAQ samples for accelerometer and current sensor data.

The downstream pipeline should not change when the acquisition adapter changes, as long as it emits the `data/README.md` schema.
