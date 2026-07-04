# Interview Walkthrough

## Thirty-Second Positioning

This is a reliability and predictive-maintenance layer for an industrial drive axis. It turns vibration, current, temperature, speed, and load telemetry into explainable diagnostic evidence, maintenance actions, validation metrics, and OT/IT integration artifacts.

## Three-Minute Technical Story

1. The simulator creates a deterministic FAT-style scenario with healthy operation and four seeded faults.
2. The quality gate checks timestamp integrity, sample gaps, nulls, duplicates, and physical ranges before analytics run.
3. Rolling windows produce vibration, current, thermal, and acoustic features.
4. A robust median/IQR baseline scores deviations from healthy behavior.
5. Diagnostic rules classify rotor imbalance, mechanical looseness, belt tension drift, and overheating.
6. Recommendations are converted into work-order-shaped maintenance actions.
7. Evidence is exported for dashboard review, InfluxDB, MQTT, and OPC UA-facing integration.

## Strong Talking Points

- The system favors explainability because maintenance teams need evidence, not just anomaly scores.
- The validation report includes detection delay, confusion matrix, fault-window recall, and healthy false-alert rate.
- Data quality is a first-class gate because bad timestamps or sensor scaling can invalidate predictive maintenance.
- The repo is CI-backed and published through GitHub Pages, so the demo is reproducible.

## Honest Limitations

- The current data is simulated and must be replaced with hardware acquisition for field claims.
- It demonstrates safety-oriented thinking, not certified safety performance.
- The rules are intentionally conservative and should be retuned with asset history.

