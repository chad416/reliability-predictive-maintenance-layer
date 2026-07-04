# Reliability and Predictive Maintenance Layer

[![CI](https://github.com/chad416/reliability-predictive-maintenance-layer/actions/workflows/ci.yml/badge.svg)](https://github.com/chad416/reliability-predictive-maintenance-layer/actions/workflows/ci.yml)
[![Pages](https://github.com/chad416/reliability-predictive-maintenance-layer/actions/workflows/pages.yml/badge.svg)](https://github.com/chad416/reliability-predictive-maintenance-layer/actions/workflows/pages.yml)

This repository is a portfolio-grade reliability engineering and predictive-maintenance layer for an industrial motion bench or material-handling micro-cell. It is intentionally more than a notebook: it includes telemetry simulation, signal feature extraction, explainable fault detection, maintenance recommendations, FMEA/FTA documentation, validation evidence, and a self-contained dashboard.

The design follows the project brief: condition monitoring for motor vibration, current, and temperature; alarm thresholds tied to measured evidence; rooted fault narratives; and maintenance actions that are useful to RAM/LCC, commissioning, quality, and connected-services teams.

## What It Demonstrates

- Industrial telemetry pipeline for vibration, current, temperature, speed, load, and acoustic data.
- Classical signal features before ML: RMS, kurtosis, crest factor, FFT 1x/2x components, broadband energy, temperature slope, and current variation.
- Robust baseline learning from healthy windows using median and IQR statistics.
- Explainable diagnostics for rotor imbalance, mechanical looseness, belt tension drift, overheating, and sensor or mounting issues.
- Maintenance action matrix with priority, inspection steps, spares, downtime class, and verification checks.
- Documentation pack: FMEA, fault tree, alarm rationalization, validation plan, FAT protocol, commissioning checklist, BOM, and OT/IT integration notes.
- Reproducible demo pipeline and built-in unit tests.
- Paced telemetry replay with batched JSONL, retrying InfluxDB, and optional MQTT delivery.
- Provisioned InfluxDB, Grafana, and Mosquitto edge stack with health checks and a schema-aligned live dashboard.

## Quick Start

Use the bundled Python runtime or any Python 3.10+ environment with `numpy` and `pandas`.

```powershell
$env:PYTHONPATH = "src"
python scripts/run_demo.py
python -m unittest discover -s tests
```

The demo creates:

- `data/simulated/mixed_faults.csv`
- `output/demo/features.csv`
- `output/demo/scored_features.csv`
- `output/demo/alerts.csv`
- `output/demo/recommendations.csv`
- `output/demo/validation_summary.csv`
- `output/demo/confusion_matrix.csv`
- `output/demo/validation_metrics.json`
- `output/demo/data_quality.json`
- `output/demo/work_orders.json`
- `output/demo/condition_windows.lp`
- `output/demo/mqtt_outbox.jsonl`
- `output/demo/opcua_snapshot.json`
- `reports/maintenance_case_report.md`
- `dashboard/index.html`

Open `dashboard/index.html` in a browser for the self-contained portfolio dashboard.

## GitHub Portfolio View

The repository includes GitHub Actions workflows for continuous validation and dashboard publishing:

- CI runs compile checks, unit tests, the full demo pipeline, and dashboard payload validation.
- The Pages workflow publishes the generated dashboard and selected evidence artifacts.
- After GitHub Pages is enabled for this repository, the portfolio dashboard is expected at:
  `https://chad416.github.io/reliability-predictive-maintenance-layer/`

## CLI Usage

```powershell
$env:PYTHONPATH = "src"
python -m rpm_layer.cli demo
python -m rpm_layer.cli simulate --out data/simulated/mixed_faults.csv
python -m rpm_layer.cli features --input data/simulated/mixed_faults.csv --out output/features.csv
python -m rpm_layer.cli baseline --features output/features.csv --out output/baseline.json
python -m rpm_layer.cli analyze --features output/features.csv --baseline output/baseline.json --out-dir output/demo
python -m rpm_layer.cli report --out-dir output/demo --report reports/maintenance_case_report.md --dashboard dashboard/index.html
python -m rpm_layer.cli replay --input data/simulated/mixed_faults.csv --max-records 100
python -m rpm_layer.cli influx-write --input output/demo/condition_windows.lp --influx-token YOUR_TOKEN
```

For the live historian and broker workflow, follow the [observability stack runbook](docs/observability_stack.md).

## Repository Map

```text
config/                 Asset profile and maintenance rules
dashboard/              Generated self-contained dashboard target
data/                   Demo data and data contracts
docs/                   Engineering documentation pack
reports/                Generated maintenance report target
scripts/                One-command demo runner
src/rpm_layer/          Predictive-maintenance package
tests/                  Unit tests using the standard library test runner
```

## Evidence Pack

The generated evidence pack is designed for engineering review:

- `reports/maintenance_case_report.md` gives the executive summary, alert episodes, maintenance actions, validation table, and confusion matrix.
- `dashboard/index.html` gives a self-contained visual review surface and is published through GitHub Pages.
- `output/demo/work_orders.json` converts recommendations into maintenance work-order shaped records.
- `output/demo/data_quality.json` records timestamp, sampling, null, duplicate, and range integrity checks.
- `output/demo/condition_windows.lp` exports condition windows in InfluxDB line protocol for historian or Grafana integration.
- `output/demo/mqtt_outbox.jsonl` shows the MQTT topic and payload contract for condition, alert, and recommendation messages.
- `output/demo/opcua_snapshot.json` shows the OPC UA-facing condition and maintenance node model.
- `docs/traceability_matrix.md` links project requirements to implementation and evidence artifacts.

## Engineering Notes For Reviewers

- [Traceability matrix](docs/traceability_matrix.md)
- [Evidence pack](docs/evidence_pack.md)
- [Field validation protocol](docs/field_validation_protocol.md)
- [Interview walkthrough](docs/interview_walkthrough.md)
- [Known limitations](docs/known_limitations.md)
- [Observability stack runbook](docs/observability_stack.md)
- [Architecture decision records](docs/adr/0001-classical-features-before-ml.md)

## Engineering Positioning

This project is meant to sit above the motion bench or material-handling cell in the wider automation portfolio. In a real deployment, acquisition would come from accelerometers, current sensing, temperature sensing, and PLC/drive telemetry over OPC UA or MQTT. This implementation includes an industrially realistic simulator so the analytics and documentation can be reviewed before hardware is connected.

The core rule is honesty: the system demonstrates reliability engineering intent, diagnostic reasoning, and validation discipline. It does not claim certified SIL/PL safety or production predictive accuracy without a certified safety chain and field validation campaign.
