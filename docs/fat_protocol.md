# FAT Protocol

## Scope

Factory acceptance testing for the reliability and predictive-maintenance layer using deterministic simulated telemetry. Hardware FAT should reuse the same structure once sensor acquisition is connected.

## Preconditions

- Python 3.10+ environment with `numpy` and `pandas`.
- Repository checked out with `src` on `PYTHONPATH`.
- Asset profile reviewed in `config/asset_profile.json`.

## Procedure

| Step | Action | Expected result | Evidence |
| --- | --- | --- | --- |
| FAT-001 | Run `python scripts/run_demo.py` | Pipeline completes without error | Console output and generated files |
| FAT-002 | Inspect `output/demo/features.csv` | Feature windows are present and no key metric is blank | CSV review |
| FAT-003 | Inspect `output/demo/alerts.csv` | Seeded conditions create alerts | CSV review |
| FAT-004 | Inspect `output/demo/recommendations.csv` | Each alert episode maps to an action | CSV review |
| FAT-005 | Open `reports/maintenance_case_report.md` | Report has executive summary, alerts, actions, validation table | Report review |
| FAT-006 | Open `dashboard/index.html` | KPIs, condition timeline, alerts, and recommendations render | Browser screenshot |
| FAT-007 | Run `python -m unittest discover -s tests` | All tests pass | Test output |

## Acceptance Criteria

- No runtime errors.
- At least one seeded fault generates a maintenance recommendation.
- All five seeded fault classes generate a diagnostic path or are explicitly reported as a validation miss.
- The report and dashboard are reproducible from source data.
- Alarm explanations include measurable evidence, not only a label.
