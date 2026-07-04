# OPC UA and MQTT Integration Notes

## OPC UA Node Model

Recommended namespace shape:

```text
Assets/
  MHC-CONV-AXIS-01/
    Telemetry/
      SpeedRpm
      LoadPct
      VibrationG
      CurrentA
      TemperatureC
    Condition/
      ConditionIndex
      ActiveDiagnosis
      ActiveSeverity
      LastRecommendation
```

## MQTT Topics

```text
factory/mhc/axis01/telemetry
factory/mhc/axis01/features
factory/mhc/axis01/alerts
factory/mhc/axis01/recommendations
```

Telemetry messages should include timestamp, asset ID, units, and sequence number. Alert messages should include evidence fields, not only severity.

## Store-and-Forward

The acquisition layer should buffer locally when the network is unavailable. Missing telemetry is itself a reliability event because the machine becomes blind to condition changes.

