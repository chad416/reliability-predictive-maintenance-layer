# Alarm Rationalization

| Alarm | Severity basis | Operator response | Maintenance response | Suppression rule |
| --- | --- | --- | --- | --- |
| Rotor imbalance warning | Diagnostic score >= warning threshold and elevated 1x vibration | Continue if stable; avoid speed increases | Inspect pulley, coupling, buildup, and balance | Suppress during known cleaning run |
| Mechanical looseness critical | High impact evidence or repeated warning windows | Controlled stop if score continues rising | Torque audit and frame inspection | Suppress only during documented maintenance test |
| Belt tension drift warning | Current and temperature trend at comparable load | Schedule planned adjustment | Check tension, tracking, rollers | Suppress during recipe/load commissioning |
| Overheating critical | Temperature score and slope above critical rule | Reduce load or stop if rising | Check cooling, fan, friction, drive limits | No suppression except sensor validation |
| Sensor or mounting advisory | Vibration anomaly without correlated process evidence | Keep running if process stable | Inspect sensor mounting and cable | Suppress after reference sensor confirms false signal |

Alarms must be actionable. If a condition is not tied to a specific inspection or verification step, it should remain a trend indicator rather than an operator alarm.

