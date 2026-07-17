# KPI Definition Sheet

| KPI | Definition | Unit | Decision use | Evidence source |
| --- | --- | --- | --- | --- |
| Condition index | Mean of positive robust feature deviations, clipped to 0-100 | 0-100 | Rank the current condition state | `output/demo/scored_features.csv` |
| Fault-window recall | Correct diagnostic windows divided by all seeded-fault windows | % | Measure detection coverage in FAT-style validation | `output/demo/validation_metrics.json` |
| Healthy false-alert rate | Healthy windows incorrectly diagnosed as a fault | % | Control nuisance alarms and operator trust | `output/demo/validation_metrics.json` |
| Detection delay | First correctly diagnosed window minus the seeded-fault start | seconds | Judge whether the alert arrives early enough for maintenance planning | `output/demo/validation_summary.csv` |
| Nuisance alarm rate | Healthy operating windows with a warning or critical alert | alarms / healthy windows | Validate speed/load variation robustness | `output/demo/validation_summary.csv` |
| Data-quality status | Pass/fail gate over timestamps, sampling, nulls, duplicates, and physical ranges | status | Prevent analytics from running on unusable telemetry | `output/demo/data_quality.json` |
| Maintenance closure | Post-action evidence returning to baseline under representative duty | pass/fail | Close the work order and govern baseline updates | `docs/field_validation_protocol.md` |

Threshold governance belongs to the asset and operating context. The demonstration values are not production limits and must be recommissioned after sensor installation.
