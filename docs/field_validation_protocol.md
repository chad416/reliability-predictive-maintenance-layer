# Field Validation Protocol

## Purpose

This protocol defines how the reliability layer should move from simulated evidence to hardware evidence on a motion bench or material-handling axis.

## Phase 1: Sensor Integrity

| Step | Action | Pass criterion |
| --- | --- | --- |
| FV-001 | Verify accelerometer orientation and mounting | No loose sensor response during tap test |
| FV-002 | Verify current telemetry scaling | Current trend matches drive or clamp reference within agreed tolerance |
| FV-003 | Verify temperature sensor placement | Temperature changes smoothly and matches expected ambient offset |
| FV-004 | Run data-quality gate | `data_quality.json` status is `pass` |

## Phase 2: Healthy Baseline

| Step | Action | Pass criterion |
| --- | --- | --- |
| FV-101 | Capture unloaded warm-up | No warning or critical diagnostics |
| FV-102 | Capture representative loaded operation | Healthy false-alert rate remains acceptable |
| FV-103 | Archive baseline | Baseline JSON is stored with asset state and date |

## Phase 3: Seeded Fault Validation

| Step | Condition | Expected result |
| --- | --- | --- |
| FV-201 | Added imbalance | Rotor imbalance diagnosis with 1x/vibration evidence |
| FV-202 | Loosened non-safety mounting point | Mechanical looseness diagnosis with broadband/impact evidence |
| FV-203 | Belt tension drift or load drag | Belt tension drift diagnosis with current-led evidence |
| FV-204 | Controlled thermal trend | Overheating diagnosis with thermal level/slope evidence |

## Phase 4: Maintenance Handover

- Review `work_orders.json` with maintenance.
- Confirm each recommendation has inspection steps, spares, and verification criteria.
- Review alarm rationalization and suppression rules.
- Decide baseline-update ownership.

