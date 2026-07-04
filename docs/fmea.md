# FMEA Worksheet

| Item | Failure mode | Effect | Cause | Detection method | Severity | Occurrence | Detection | RPN | Mitigation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Motor or pulley | Rotor imbalance | Increasing vibration, bearing wear, product handling instability | Buildup, damaged pulley, asymmetric load | 1x FFT amplitude, vibration RMS trend | 7 | 4 | 3 | 84 | Clean, inspect, balance, verify 1x reduction |
| Motor frame | Mechanical looseness | Impact loading, fatigue, sensor false alarms, possible mount failure | Loose fasteners, cracked bracket, poor base | Crest factor, kurtosis, broadband vibration | 8 | 3 | 3 | 72 | Torque audit, mark fasteners, inspect frame |
| Conveyor belt | Belt tension drift | Slip, overheating, degraded throughput | Stretch, misalignment, roller drag | Current rise at similar load, temperature trend | 6 | 5 | 4 | 120 | Adjust tension, inspect rollers, trend current |
| Drive or motor | Overheating | Thermal trip, insulation degradation, unplanned stop | High duty cycle, blocked cooling, friction | Temperature threshold and slope | 8 | 3 | 2 | 48 | Check cooling, duty cycle, drive limits |
| Accelerometer chain | Sensor mounting issue | False maintenance work order or missed fault | Loose sensor, cable shielding, bad grounding | Vibration anomaly without current/thermal correlation | 5 | 4 | 4 | 80 | Mount inspection, cable strain relief, reference sensor |
| Acquisition service | Lost telemetry | Blind operation, no condition trend | Network dropout, process crash | Missing samples, stale timestamp watchdog | 6 | 3 | 2 | 36 | Heartbeat, local buffering, restart policy |

## Notes

RPN values are demonstration values for a portfolio lab. They should be recalibrated with field history, asset criticality, and maintenance records before production use.

