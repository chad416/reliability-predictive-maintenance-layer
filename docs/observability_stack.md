# Observability Stack Runbook

## Scope

The local edge stack provides InfluxDB 2 for time-series storage, Grafana for condition monitoring, and Mosquitto for MQTT transport. It is an engineering demonstration stack, not a safety function or a production security baseline.

## Start And Seed

1. Copy `.env.example` to `.env` and replace every example credential.
2. Generate the deterministic evidence with `python scripts/run_demo.py`.
3. Start the services with `docker compose up -d influxdb grafana mqtt`.
4. Load condition windows with `docker compose --profile seed run --rm seed`.
5. Open Grafana at `http://localhost:3000` and select **Predictive Maintenance / Reliability and Predictive Maintenance Layer**.

The datasource and dashboard are provisioned automatically. InfluxDB is exposed at `http://localhost:8086`; MQTT listens at `localhost:1883`.

## Publish From The CLI

Upload generated condition windows directly:

```powershell
$env:INFLUXDB_TOKEN = "the-token-from-your-env-file"
python -m rpm_layer.cli influx-write --input output/demo/condition_windows.lp
```

Replay raw acquisition samples to the historian and a local audit file:

```powershell
python -m rpm_layer.cli replay `
  --input data/simulated/mixed_faults.csv `
  --sink jsonl --sink influx `
  --jsonl-out output/replay/telemetry.jsonl `
  --speed 20
```

Publish to MQTT after installing `pip install -e .[mqtt]`:

```powershell
python -m rpm_layer.cli replay --sink mqtt --mqtt-host localhost --speed 20
```

Use `--speed 1` for wall-clock replay and `--speed 0` for an unpaced commissioning smoke test. `--max-records` limits a test without modifying source data.

## Acceptance Checks

- `docker compose ps` reports all three long-running services healthy.
- Grafana datasource **InfluxDB Maintenance** reports a successful connection.
- The condition dashboard shows condition index, vibration, electrical, thermal, and diagnostic-state data.
- MQTT subscribers receive ordered telemetry under `factory/mhc/<asset_id>/telemetry`.
- Stopping the historian causes the CLI to fail after three bounded write attempts rather than silently dropping data.

## Security Boundary

The checked-in defaults are for an isolated demonstration network. Before use on an OT network, replace credentials, disable anonymous MQTT access, enable TLS, restrict exposed ports, store secrets outside Compose files, and apply the site firewall and certificate policy.
