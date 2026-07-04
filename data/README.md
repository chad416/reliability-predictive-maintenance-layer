# Data Contract

The acquisition layer writes one row per sample. Hardware integrations should preserve these columns so the feature and diagnostic pipeline can run without code changes.

| Column | Unit | Description |
| --- | --- | --- |
| `timestamp` | ISO-8601 UTC-like local timestamp | Sample time |
| `asset_id` | text | Stable asset identifier |
| `speed_rpm` | rpm | Shaft or commanded drive speed |
| `load_pct` | percent | Estimated process load |
| `vibration_g` | g | Acceleration magnitude or selected vibration axis |
| `current_a` | ampere | Motor phase/current telemetry or drive estimate |
| `temperature_c` | deg C | Motor frame, gearbox, or drive thermal reading |
| `acoustic_db` | dB | Optional acoustic condition indicator |
| `fault_label` | text | Optional validation label for seeded test cases |
| `fault_severity` | 0-1 | Optional seeded severity for validation |

For real hardware, leave `fault_label` as `unknown` unless the test procedure intentionally seeds a fault.

