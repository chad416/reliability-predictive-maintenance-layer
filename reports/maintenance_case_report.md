# Predictive Maintenance Case Report

## Executive Summary

The reliability layer analyzed 240 diagnostic windows and produced 132 alert windows. The maximum condition index was 75.9/100, with 61 critical windows. Window accuracy is 97.5%, seeded-fault window recall is 95.7%, and the healthy false-alert rate is 0.0%.

This report is designed as FAT-style evidence for a portfolio review: it shows the seeded condition, the features used to detect it, the resulting diagnosis, and the maintenance response.

## Data Quality Gate

Telemetry quality status is pass; estimated sampling is 120.00 Hz with a maximum sample gap of 8.33 ms.

## Alert Episodes

| diagnosis | severity | first_seen | last_seen | windows | max_score | max_condition_index | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| belt_tension_drift | critical | 2026-07-01T08:13:50 | 2026-07-01T08:15:59.991667 | 26 | 24.807 | 75.88 | current_load_normalized_a=4.3796 (robust_score=2.988); vib_low_frequency_peak_g=0.037834 (robust_score=65.591); temperature_mean_c=35.68 (robust_score=2.374) |
| mechanical_looseness | critical | 2026-07-01T08:09:50 | 2026-07-01T08:12:39.991667 | 34 | 9.712 | 63.46 | vib_kurtosis=5.7232 (robust_score=-0.836); vib_crest_factor=5.617 (robust_score=-1.105); vib_broadband_g=0.006167 (robust_score=20.126) |
| rotor_imbalance | critical | 2026-07-01T08:04:00 | 2026-07-01T08:06:59.991667 | 36 | 19.046 | 40.75 | vib_fft_1x_g=0.1013 (robust_score=15.641); vib_rms_g=0.07682 (robust_score=21.040); current_mean_a=2.2342 (robust_score=0.672) |
| elevated_friction | critical | 2026-07-01T08:16:00 | 2026-07-01T08:17:09.991667 | 14 | 7.928 | 29.11 | current_load_normalized_a=4.7684 (robust_score=4.170); vib_friction_peak_g=0.011487 (robust_score=14.043); temperature_slope_c_per_min=3.5743 (robust_score=5.381) |
| overheating | critical | 2026-07-01T08:17:30 | 2026-07-01T08:19:19.991667 | 22 | 6.892 | 23.98 | temperature_mean_c=42.823 (robust_score=7.056); temperature_slope_c_per_min=5.6972 (robust_score=8.630); current_mean_a=2.1638 (robust_score=0.375) |

## Maintenance Action Matrix

| priority | diagnosis | severity | downtime_class | recommended_action | spares | verification |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | mechanical_looseness | critical | controlled_stop_required | Inspect motor mount, gearbox base, bearing housing, sensor bracket, and frame fasteners; torque and mark hardware. | mounting fasteners, thread locker, sensor mounting pad | Crest factor and broadband energy return to baseline after torque check. |
| P1 | elevated_friction | critical | controlled_stop_if_rising | Inspect rollers, bearings, belt tracking, guards, and product drag; remove the source of mechanical resistance before returning to full duty. | idler roller, bearing insert, belt cleaner | Load-normalized current and temperature slope return to baseline across two representative duty cycles. |
| P1 | overheating | critical | controlled_stop_if_rising | Check ventilation, duty cycle, current draw, ambient temperature, drive thermal limits, and mechanical friction. | fan, filter, thermal sensor | Temperature stabilizes below warning threshold under representative load. |
| P2 | belt_tension_drift | critical | planned_adjustment | Check belt tension, tracking, roller drag, and product accumulation; adjust tension and verify current draw. | belt, idler roller, tensioner hardware | Load-normalized current returns to baseline and no new temperature rise appears. |
| P2 | rotor_imbalance | critical | planned_short_stop | Inspect pulley, coupling, fan, and carried load symmetry; clean buildup; balance rotating element if evidence persists. | coupling insert, pulley key, balancing weights | 1x vibration amplitude returns within 2.5 robust baseline units for two production cycles. |

## Validation Detection Summary

| validation_label | expected_diagnosis | windows | detected_windows | detection_rate_pct | first_detection | detection_delay_s |
| --- | --- | --- | --- | --- | --- | --- |
| healthy | healthy | 102 | 102 | 100.0 | 2026-07-01T08:00:00 | 0.0 |
| imbalance | rotor_imbalance | 36 | 36 | 100.0 | 2026-07-01T08:04:00 | 0.0 |
| loose_mounting | mechanical_looseness | 40 | 34 | 85.0 | 2026-07-01T08:09:50 | 30.0 |
| belt_tension_drift | belt_tension_drift | 26 | 26 | 100.0 | 2026-07-01T08:13:50 | 0.0 |
| elevated_friction | elevated_friction | 14 | 14 | 100.0 | 2026-07-01T08:16:00 | 0.0 |
| overheating | overheating | 22 | 22 | 100.0 | 2026-07-01T08:17:30 | 0.0 |

## Confusion Matrix

| expected_diagnosis | healthy | rotor_imbalance | mechanical_looseness | belt_tension_drift | elevated_friction | overheating |
| --- | --- | --- | --- | --- | --- | --- |
| healthy | 102 | 0 | 0 | 0 | 0 | 0 |
| rotor_imbalance | 0 | 36 | 0 | 0 | 0 | 0 |
| mechanical_looseness | 6 | 0 | 34 | 0 | 0 | 0 |
| belt_tension_drift | 0 | 0 | 0 | 26 | 0 | 0 |
| elevated_friction | 0 | 0 | 0 | 0 | 14 | 0 |
| overheating | 0 | 0 | 0 | 0 | 0 | 22 |

## Engineering Notes

- The baseline is fitted from healthy windows using robust median/IQR statistics, which is appropriate for commissioning data that may include noise and non-Gaussian process variation.
- The diagnostic layer uses explainable rule scores rather than opaque model output. This is intentional for maintenance acceptance: every alarm must be traceable to evidence an engineer can inspect.
- The current implementation is ready for OPC UA or MQTT acquisition adapters. The CSV data contract is stable and documented in `data/README.md`.
- The system demonstrates safety-oriented and reliability-engineering thinking, but it does not claim certified safety performance or production predictive accuracy without hardware validation.
