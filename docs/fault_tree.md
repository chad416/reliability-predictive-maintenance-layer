# Fault Tree

Top event: conveyor drive axis unavailable or operating in degraded condition.

```mermaid
flowchart TD
  Top["Drive axis degraded or unavailable"] --> Vib["Excessive vibration"]
  Top --> Thermal["Thermal overload risk"]
  Top --> Telemetry["Condition monitoring blind spot"]
  Vib --> Imbalance["Rotor or pulley imbalance"]
  Vib --> Loose["Mechanical looseness"]
  Vib --> Belt["Belt tension or roller drag"]
  Thermal --> Cooling["Blocked cooling or fan issue"]
  Thermal --> Load["Sustained high load or duty cycle"]
  Thermal --> Friction["Mechanical friction"]
  Telemetry --> Sensor["Sensor mounting or cable fault"]
  Telemetry --> Network["Acquisition or network dropout"]
```

## Diagnostic Linkage

- Imbalance is expected to show a dominant 1x shaft-frequency component.
- Looseness is expected to show high crest factor, kurtosis, and broadband vibration.
- Belt tension drift is expected to show current increase at comparable load and speed.
- Overheating is expected to show thermal threshold crossing or positive temperature slope.
- Sensor issues are suspected when vibration evidence is not supported by current, thermal, or acoustic correlation.

