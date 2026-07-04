# ADR 0003: Static Dashboard And Evidence Pack

## Status

Accepted

## Context

The project must be reviewable by recruiters and engineering managers without requiring Docker, Grafana, InfluxDB, or hardware access.

## Decision

The demo generates a self-contained HTML dashboard and static evidence files. CI regenerates them, and GitHub Pages publishes the latest review surface.

## Consequences

- The portfolio is easy to inspect from a browser.
- The same pipeline can still export InfluxDB line protocol, MQTT messages, and OPC UA node snapshots for industrial integration.
- The static dashboard is not a substitute for a production SCADA or historian deployment.

