# Known Limitations

- The telemetry is simulated. It is useful for FAT-style validation and portfolio review, but it is not field performance evidence.
- Diagnostic thresholds are tuned for the demonstration asset profile and must be recommissioned per asset class.
- The dashboard is static. Production deployments should use a historian, SCADA, or observability stack.
- MQTT and OPC UA outputs are integration contracts, not live broker/server implementations.
- Safety-related claims are limited to engineering intent and diagnostic support. This project does not certify SIL, PL, or machine safety functions.

