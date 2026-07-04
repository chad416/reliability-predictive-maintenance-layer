# Predictive Maintenance Case Report

## Executive Summary

The reliability layer analyzed 239 diagnostic windows and produced 119 alert windows. The maximum condition index was 51.6/100, with 31 critical windows. Window accuracy is 90.4%, seeded-fault window recall is 83.8%, and the healthy false-alert rate is 0.0%.

This report is designed as FAT-style evidence for a portfolio review: it shows the seeded condition, the features used to detect it, the resulting diagnosis, and the maintenance response.

## Alert Episodes

| diagnosis | severity | first_seen | last_seen | windows | max_score | max_condition_index | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mechanical_looseness | critical | 2026-07-01T08:09:50 | 2026-07-01T08:12:39.991000 | 34 | 9.967 | 51.58 | score_vib_kurtosis=-0.809; score_vib_crest_factor=-1.083; score_vib_broadband_g=20.974 |
| rotor_imbalance | critical | 2026-07-01T08:04:00 | 2026-07-01T08:06:59.991000 | 36 | 18.845 | 45.33 | score_vib_fft_1x_g=15.537; score_vib_rms_g=20.713; score_current_mean_a=0.643 |
| overheating | critical | 2026-07-01T08:17:00 | 2026-07-01T08:19:19.991000 | 28 | 7.047 | 26.13 | score_temperature_mean_c=7.862; score_temperature_slope_c_per_min=7.663; score_current_mean_a=0.35 |
| belt_tension_drift | warning | 2026-07-01T08:14:55 | 2026-07-01T08:16:49.991000 | 21 | 3.29 | 22.47 | score_current_mean_a=3.469; score_temperature_mean_c=1.892; score_vib_broadband_g=5.428 |

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
| healthy | healthy | 97 | 97 | 100.0 | 2026-07-01T08:00:00 | 0.0 |
| imbalance | rotor_imbalance | 36 | 36 | 100.0 | 2026-07-01T08:04:00 | 0.0 |
| loose_mounting | mechanical_looseness | 40 | 34 | 85.0 | 2026-07-01T08:09:50 | 30.0 |
| belt_tension_drift | belt_tension_drift | 36 | 21 | 58.33 | 2026-07-01T08:14:55 | 65.0 |
| overheating | overheating | 30 | 28 | 93.33 | 2026-07-01T08:17:00 | 10.0 |

## Confusion Matrix

| expected_diagnosis | healthy | rotor_imbalance | mechanical_looseness | belt_tension_drift | overheating |
| --- | --- | --- | --- | --- | --- |
| healthy | 97 | 0 | 0 | 0 | 0 |
| rotor_imbalance | 0 | 36 | 0 | 0 | 0 |
| mechanical_looseness | 6 | 0 | 34 | 0 | 0 |
| belt_tension_drift | 15 | 0 | 0 | 21 | 0 |
| overheating | 2 | 0 | 0 | 0 | 28 |

## Engineering Notes

- The baseline is fitted from healthy windows using robust median/IQR statistics, which is appropriate for commissioning data that may include noise and non-Gaussian process variation.
- The diagnostic layer uses explainable rule scores rather than opaque model output. This is intentional for maintenance acceptance: every alarm must be traceable to evidence an engineer can inspect.
- The current implementation is ready for OPC UA or MQTT acquisition adapters. The CSV data contract is stable and documented in `data/README.md`.
- The system demonstrates safety-oriented and reliability-engineering thinking, but it does not claim certified safety performance or production predictive accuracy without hardware validation.
