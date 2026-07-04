# Validation Plan

## Objectives

1. Prove the pipeline detects seeded faults with explainable evidence.
2. Measure nuisance alerts during healthy speed and load changes.
3. Confirm reports and dashboards match the generated analysis artifacts.
4. Preserve a repeatable test sequence for portfolio demonstration and future hardware bring-up.

## Seeded Fault Tests

| Test | Seeded condition | Expected evidence | Pass criteria |
| --- | --- | --- | --- |
| VAL-001 | Healthy operation with speed/load variation | Low condition index, no repeated warning | No warning or critical episode |
| VAL-002 | Rotor imbalance | Elevated 1x FFT and vibration RMS | Rotor imbalance warning before end of segment |
| VAL-003 | Loose mounting | Crest factor, kurtosis, broadband vibration | Mechanical looseness alert generated |
| VAL-004 | Belt tension drift | Load-normalized current and thermal rise | Belt tension drift recommendation generated |
| VAL-005 | Overheating | Temperature mean and slope | Overheating warning or critical alert generated |
| VAL-006 | Sensor mounting issue | Vibration evidence without process correlation | Sensor issue recommendation generated when seeded in future acquisition tests |

## Metrics

- Detection delay by condition.
- Alert window count by severity.
- False alert count during healthy windows.
- Maximum condition index.
- Completeness of recommendation fields: action, inspection, spares, downtime, verification.

