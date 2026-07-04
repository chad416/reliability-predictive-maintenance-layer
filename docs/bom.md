# Indicative BOM

| Category | Example | Purpose |
| --- | --- | --- |
| Vibration sensor | ADXL356 or ADXL355-class low-noise accelerometer | Motor or gearbox condition monitoring |
| Current sensing | Hall-effect current sensor or drive telemetry | Load-normalized current trend |
| Temperature sensing | RTD, thermistor, or drive thermal telemetry | Overheating and friction trend |
| Edge compute | Industrial PC, Raspberry Pi, or Jetson-class edge device | Acquisition, buffering, analytics |
| OT connectivity | OPC UA client or MQTT edge gateway | PLC/SCADA integration |
| Dashboard stack | Grafana and InfluxDB optional deployment | Operations visualization |
| Reference tools | Torque wrench, tachometer, handheld vibration meter | Commissioning verification |

The software in this repository runs without the hardware BOM by using deterministic simulated telemetry.

