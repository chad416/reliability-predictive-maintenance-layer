# Portfolio Presentation Plan

## One-Minute Demo

1. Show the dashboard KPI cards and condition timeline.
2. Point to a seeded imbalance, looseness, or friction episode and show the raw feature plus robust score.
3. Open the maintenance recommendation and evidence fields.
4. State how the same pipeline connects to OPC UA or MQTT telemetry from the motion bench or material-handling cell.

Use the three SVGs under `docs/assets/` as the repository and portfolio thumbnail set. They explain the architecture, the diagnostic evidence chain, and the maintenance closure loop without requiring the reviewer to read the full codebase.

## Six-Minute Engineering Walkthrough

1. Asset profile and sensor plan.
2. Data contract and acquisition boundary.
3. Feature extraction choices: RMS, kurtosis, crest factor, FFT 1x/2x, temperature slope, current trend.
4. Baseline learning and why median/IQR is used.
5. Diagnostic rules and alarm rationalization.
6. FMEA/FTA and validation evidence.
7. What changes when real hardware is connected.

## Interview Talking Points

- Explainability matters more than fashionable ML for first maintenance acceptance.
- Predictive maintenance is only useful when it closes the loop into work orders, spares, and verification.
- Baselines are engineering artifacts and need governance.
- False positives damage trust, so nuisance alarms must be measured and controlled.
