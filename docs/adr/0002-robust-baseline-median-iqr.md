# ADR 0002: Robust Median/IQR Baseline

## Status

Accepted

## Context

Commissioning data can include speed changes, load variation, sensor noise, and occasional transient behavior. A mean/std baseline is vulnerable to those outliers.

## Decision

Healthy behavior is represented by per-feature median and interquartile range. Scores are robust deviations from the healthy baseline.

## Consequences

- The baseline is stable during early commissioning.
- Operators can understand a feature score as deviation from normal behavior.
- Baseline updates must be governed; they should happen only after maintenance verification confirms the asset is healthy.

