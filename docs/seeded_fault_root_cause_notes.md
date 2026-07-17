# Seeded Fault Root-Cause Notes

These notes explain the diagnostic chain used by the deterministic simulator. They are engineering hypotheses and FAT-style evidence, not proof of field causality.

| Seeded condition | Measured symptom pattern | Diagnostic evidence | Maintenance response | Verification |
| --- | --- | --- | --- | --- |
| Rotor imbalance | Dominant 1x shaft-frequency vibration, higher RMS, mild current increase | `vib_fft_1x_g`, `vib_rms_g`, current score | Inspect pulley/coupling, clean buildup, check runout, balance if persistent | 1x amplitude returns near baseline for two representative cycles |
| Loose mounting | Impact-like vibration, crest-factor/kurtosis change, broadband energy | `vib_crest_factor`, `vib_kurtosis`, `vib_broadband_g` | Torque audit, inspect frame/bracket, verify accelerometer mounting | Broadband energy and crest factor return to baseline after torque check |
| Belt-tension drift | Current rise at comparable load, moderate thermal and low-frequency vibration response | `current_load_normalized_a`, `vib_low_frequency_peak_g`, temperature | Inspect tension, tracking, rollers, and product accumulation | Load-normalized current returns to baseline without a new thermal rise |
| Elevated friction | Current rise that persists after load normalization, a low-frequency friction signature, and positive temperature slope | `current_load_normalized_a`, `vib_friction_peak_g`, `temperature_slope_c_per_min` | Inspect rollers, bearings, guards, belt tracking, and product drag | Current and thermal slope normalize across unloaded and loaded cycles |
| Overheating trend | Temperature level and slope rise with sustained duty | temperature mean, temperature slope, current | Check cooling path, fan, drive limits, duty cycle, and mechanical friction | Temperature stabilizes below warning threshold under representative load |

## Diagnostic discipline

The classifier reports the strongest rule score, but the evidence string also carries the raw feature value and its robust baseline score. That keeps the alarm explainable: a reviewer can distinguish an absolute measurement from a deviation score and can see where a false positive should be investigated.
