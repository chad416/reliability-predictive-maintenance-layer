# Predictive Maintenance Case Report

## Executive Summary

The reliability layer analyzed 240 diagnostic windows and produced 119 alert windows. The maximum condition index was 50.7/100, with 31 critical windows. Window accuracy is 90.4%, seeded-fault window recall is 83.8%, and the healthy false-alert rate is 0.0%.

This report is designed as FAT-style evidence for a portfolio review: it shows the seeded condition, the features used to detect it, the resulting diagnosis, and the maintenance response.

## Data Quality Gate

Telemetry quality status is pass; estimated sampling is 120.00 Hz with a maximum sample gap of 8.33 ms.

## Alert Episodes

| diagnosis | severity | first_seen | last_seen | windows | max_score | max_condition_index | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mechanical_looseness | critical | 2026-07-01T08:09:50 | 2026-07-01T08:12:39.991667 | 34 | 9.644 | 50.69 | score_vib_kurtosis=-0.813; score_vib_crest_factor=-1.084; score_vib_broadband_g=20.126 |
| rotor_imbalance | critical | 2026-07-01T08:04:00 | 2026-07-01T08:06:59.991667 | 36 | 18.833 | 45.05 | score_vib_fft_1x_g=15.634; score_vib_rms_g=20.504; score_current_mean_a=0.65 |
| overheating | critical | 2026-07-01T08:17:00 | 2026-07-01T08:19:19.991667 | 28 | 7.036 | 25.97 | score_temperature_mean_c=7.906; score_temperature_slope_c_per_min=7.546; score_current_mean_a=0.359 |
| belt_tension_drift | warning | 2026-07-01T08:14:55 | 2026-07-01T08:16:49.991667 | 21 | 3.247 | 22.15 | score_current_mean_a=3.453; score_temperature_mean_c=1.894; score_vib_broadband_g=5.199 |

## Maintenance Action Matrix

| priority | diagnosis | severity | downtime_class | recommended_action | spares | verification |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | mechanical_looseness | critical | controlled_stop_required | Inspect motor mount, gearbox base, bearing housing, sensor bracket, and frame fasteners; torque and mark hardware. | mounting fasteners, thread locker, sensor mounting pad | Crest factor and broadband energy return to baseline after torque check. |
| P1 | overheating | critical | controlled_stop_if_rising | Check ventilation, duty cycle, current draw, ambient temperature, drive thermal limits, and mechanical friction. | fan, filter, thermal sensor | Temperature stabilizes below warning threshold under representative load. |
| P2 | rotor_imbalance | critical | planned_short_stop | Inspect pulley, coupling, fan, and carried load symmetry; clean buildup; balance rotating element if evidence persists. | coupling insert, pulley key, balancing weights | 1x vibration amplitude returns within 2.5 robust baseline units for two production cycles. |
| P2 | belt_tension_drift | warning | planned_adjustment | Check belt tension, tracking, roller drag, and product accumulation; adjust tension and verify current draw. | belt, idler roller, tensioner hardware | Load-normalized current returns to baseline and no new temperature rise appears. |

## Validation Detection Summary

| validation_label | expected_diagnosis | windows | detected_windows | detection_rate_pct | first_detection | detection_delay_s |
| --- | --- | --- | --- | --- | --- | --- |
| healthy | healthy | 98 | 98 | 100.0 | 2026-07-01T08:00:00 | 0.0 |
| imbalance | rotor_imbalance | 36 | 36 | 100.0 | 2026-07-01T08:04:00 | 0.0 |
| loose_mounting | mechanical_looseness | 40 | 34 | 85.0 | 2026-07-01T08:09:50 | 30.0 |
| belt_tension_drift | belt_tension_drift | 36 | 21 | 58.33 | 2026-07-01T08:14:55 | 65.0 |
| overheating | overheating | 30 | 28 | 93.33 | 2026-07-01T08:17:00 | 10.0 |

## Confusion Matrix

| expected_diagnosis | healthy | rotor_imbalance | mechanical_looseness | belt_tension_drift | overheating |
| --- | --- | --- | --- | --- | --- |
| healthy | 98 | 0 | 0 | 0 | 0 |
| rotor_imbalance | 0 | 36 | 0 | 0 | 0 |
| mechanical_looseness | 6 | 0 | 34 | 0 | 0 |
| belt_tension_drift | 15 | 0 | 0 | 21 | 0 |
| overheating | 2 | 0 | 0 | 0 | 28 |

## Engineering Notes

- The baseline is fitted from healthy windows using robust median/IQR statistics, which is appropriate for commissioning data that may include noise and non-Gaussian process variation.
- The diagnostic layer uses explainable rule scores rather than opaque model output. This is intentional for maintenance acceptance: every alarm must be traceable to evidence an engineer can inspect.
- The current implementation is ready for OPC UA or MQTT acquisition adapters. The CSV data contract is stable and documented in `data/README.md`.
- The system demonstrates safety-oriented and reliability-engineering thinking, but it does not claim certified safety performance or production predictive accuracy without hardware validation.
