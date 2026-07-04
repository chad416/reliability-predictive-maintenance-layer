# Known Limitations

- The telemetry is simulated. It is useful for FAT-style validation and portfolio review, but it is not field performance evidence.
- Diagnostic thresholds are tuned for the demonstration asset profile and must be recommissioned per asset class.
- The public dashboard is static; the repository also includes a provisioned InfluxDB/Grafana stack for local or edge deployment.
- MQTT telemetry publishing is implemented, while the OPC UA output remains a supervisory node-model contract rather than a live server.
- Container configuration is CI-validated, but final runtime acceptance still requires Docker and a field-connected edge host.
- Safety-related claims are limited to engineering intent and diagnostic support. This project does not certify SIL, PL, or machine safety functions.
