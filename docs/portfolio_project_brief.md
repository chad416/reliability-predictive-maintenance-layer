# Portfolio Project Brief

## Title

Reliability and Predictive-Maintenance Layer

## One-line description

A software-complete reliability engineering layer for a motion-bench or conveyor drive axis: it turns industrial telemetry into explainable condition alarms, maintenance actions, and validation evidence before physical sensors are commissioned.

## Recruiter-facing proof

- Classical signal features first: RMS, kurtosis, crest factor, FFT 1x/2x, broadband vibration, temperature slope, and load-normalized current.
- Deterministic seeded scenarios: imbalance, loose mounting, belt-tension drift, elevated friction, and overheating.
- Robust median/IQR baselining, alarm severity rules, alarm rationalization, FMEA, FTA, work-order exports, and spare-parts recommendations.
- InfluxDB line protocol, MQTT messages, an OPC UA-facing node snapshot, durable SQLite store-and-forward, and provisioned Grafana dashboards.
- Static dashboard, case report, confusion matrix, detection delay, nuisance-alarm checks, and a field-validation protocol.

## Hardware boundary

The software/simulation/documentation layer is portfolio-ready. Physical ADXL355/ADXL356-class vibration sensing, current/temperature wiring, mounting verification, and measured baseline commissioning remain Phase 2. The project does not claim physical commissioning, certified SIL/PL/CE validation, or field predictive accuracy.

## Suggested portfolio links

- Live evidence dashboard: `dashboard/index.html` or the published GitHub Pages site.
- Engineering case report: `reports/maintenance_case_report.md`.
- Visual architecture: `docs/assets/reliability_architecture.svg`.
- Diagnostic evidence map: `docs/assets/diagnostic_evidence.svg`.
- Maintenance loop: `docs/assets/maintenance_loop.svg`.
