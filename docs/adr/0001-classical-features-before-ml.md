# ADR 0001: Classical Signal Features Before ML

## Status

Accepted

## Context

Predictive-maintenance projects often jump directly to opaque anomaly models. That is risky in industrial maintenance because technicians and reliability engineers need evidence they can inspect before opening work orders or stopping equipment.

## Decision

The first production-facing layer uses explainable features: vibration RMS, crest factor, kurtosis, shaft-frequency FFT components, broadband vibration, current trend, and temperature slope. ML can be added later only after enough labeled field history exists.

## Consequences

- Alarms are easier to rationalize and defend.
- False positives can be traced to specific evidence fields.
- The system remains credible without claiming unvalidated predictive accuracy.
- Model complexity is postponed until data volume and label quality justify it.

