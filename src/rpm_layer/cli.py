from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from rpm_layer.baseline import fit_baseline, load_baseline, save_baseline, score_features
from rpm_layer.config import PROJECT_ROOT, load_asset_profile, load_json
from rpm_layer.dashboard import write_dashboard
from rpm_layer.detector import aggregate_alerts, attach_predictions, detect_alerts, write_alerts
from rpm_layer.exporters import write_influx_line_protocol, write_mqtt_outbox, write_opcua_snapshot, write_work_orders
from rpm_layer.features import extract_features, read_telemetry, write_features
from rpm_layer.models import AssetProfile
from rpm_layer.quality import write_quality_report
from rpm_layer.recommender import build_recommendations, write_recommendations
from rpm_layer.reporting import write_markdown_report
from rpm_layer.simulator import generate_telemetry, write_telemetry
from rpm_layer.streaming import (
    FanoutSink,
    InfluxTelemetrySink,
    InfluxWriter,
    JsonlSink,
    MqttTelemetrySink,
    replay_telemetry,
)
from rpm_layer.validation import validation_metrics, validation_summary, write_validation_artifacts


def _profile(path: str | Path) -> AssetProfile:
    return AssetProfile.from_mapping(load_asset_profile(path))


def cmd_simulate(args: argparse.Namespace) -> None:
    profile = _profile(args.profile)
    telemetry = generate_telemetry(
        profile=profile,
        duration_s=args.duration_sec,
        sampling_hz=args.sampling_hz or profile.sampling_hz,
        seed=args.seed,
    )
    write_telemetry(telemetry, args.out)
    print(f"Wrote telemetry: {args.out} ({len(telemetry)} samples)")


def cmd_features(args: argparse.Namespace) -> None:
    profile = _profile(args.profile)
    telemetry = read_telemetry(args.input)
    features = extract_features(
        telemetry,
        sampling_hz=args.sampling_hz or profile.sampling_hz,
        window_s=args.window_sec,
        step_s=args.step_sec,
    )
    write_features(features, args.out)
    print(f"Wrote features: {args.out} ({len(features)} windows)")


def cmd_baseline(args: argparse.Namespace) -> None:
    features = pd.read_csv(args.features)
    baseline = fit_baseline(features)
    save_baseline(baseline, args.out)
    print(f"Wrote baseline: {args.out} ({baseline['healthy_window_count']} healthy windows)")


def cmd_analyze(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    features = pd.read_csv(args.features)
    baseline = load_baseline(args.baseline)
    scored = score_features(features, baseline)
    alerts = detect_alerts(scored)
    scored = attach_predictions(scored, alerts)
    aggregated = aggregate_alerts(alerts)
    recommendations = build_recommendations(aggregated)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_features(scored, out_dir / "scored_features.csv")
    write_alerts(alerts, out_dir / "alerts.csv")
    write_alerts(aggregated, out_dir / "alert_episodes.csv")
    write_recommendations(recommendations, out_dir / "recommendations.csv")
    write_validation_artifacts(scored, out_dir)
    write_work_orders(recommendations, out_dir / "work_orders.json")
    write_influx_line_protocol(scored, out_dir / "condition_windows.lp")
    write_mqtt_outbox(scored, alerts, recommendations, out_dir / "mqtt_outbox.jsonl")
    write_opcua_snapshot(scored, alerts, recommendations, out_dir / "opcua_snapshot.json")
    print(f"Wrote analysis artifacts under: {out_dir}")


def cmd_report(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    scored = pd.read_csv(out_dir / "scored_features.csv")
    alerts = pd.read_csv(out_dir / "alerts.csv") if (out_dir / "alerts.csv").exists() else pd.DataFrame()
    aggregated = pd.read_csv(out_dir / "alert_episodes.csv") if (out_dir / "alert_episodes.csv").exists() else pd.DataFrame()
    recommendations = pd.read_csv(out_dir / "recommendations.csv")
    summary = pd.read_csv(out_dir / "validation_summary.csv") if (out_dir / "validation_summary.csv").exists() else validation_summary(scored)
    metrics = validation_metrics(scored)
    quality = load_json(out_dir / "data_quality.json") if (out_dir / "data_quality.json").exists() else {}
    write_markdown_report(scored, alerts, aggregated, recommendations, args.report, quality)
    write_dashboard(scored, alerts, recommendations, args.dashboard, summary, metrics, quality)
    print(f"Wrote report: {args.report}")
    print(f"Wrote dashboard: {args.dashboard}")


def cmd_demo(args: argparse.Namespace) -> None:
    profile_path = Path(args.profile)
    out_dir = Path(args.out_dir)
    telemetry_path = Path(args.telemetry)
    feature_path = out_dir / "features.csv"
    baseline_path = out_dir / "baseline.json"

    profile = _profile(profile_path)
    telemetry = generate_telemetry(profile=profile, duration_s=args.duration_sec, sampling_hz=profile.sampling_hz, seed=args.seed)
    write_telemetry(telemetry, telemetry_path)
    quality = write_quality_report(telemetry, profile.sampling_hz, out_dir / "data_quality.json")
    features = extract_features(telemetry, sampling_hz=profile.sampling_hz)
    write_features(features, feature_path)
    baseline = fit_baseline(features)
    save_baseline(baseline, baseline_path)
    scored = score_features(features, baseline)
    alerts = detect_alerts(scored)
    scored = attach_predictions(scored, alerts)
    aggregated = aggregate_alerts(alerts)
    recommendations = build_recommendations(aggregated)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_features(scored, out_dir / "scored_features.csv")
    write_alerts(alerts, out_dir / "alerts.csv")
    write_alerts(aggregated, out_dir / "alert_episodes.csv")
    write_recommendations(recommendations, out_dir / "recommendations.csv")
    summary, _, metrics = write_validation_artifacts(scored, out_dir)
    write_work_orders(recommendations, out_dir / "work_orders.json")
    write_influx_line_protocol(scored, out_dir / "condition_windows.lp")
    write_mqtt_outbox(scored, alerts, recommendations, out_dir / "mqtt_outbox.jsonl")
    write_opcua_snapshot(scored, alerts, recommendations, out_dir / "opcua_snapshot.json")
    write_markdown_report(scored, alerts, aggregated, recommendations, args.report, quality)
    write_dashboard(scored, alerts, recommendations, args.dashboard, summary, metrics, quality)

    print(f"Telemetry: {telemetry_path}")
    print(f"Features: {feature_path}")
    print(f"Alerts: {out_dir / 'alerts.csv'}")
    print(f"Report: {args.report}")
    print(f"Dashboard: {args.dashboard}")


def cmd_replay(args: argparse.Namespace) -> None:
    telemetry = read_telemetry(args.input)
    selected_sinks = args.sink or ["jsonl"]
    token = args.influx_token or os.environ.get("INFLUXDB_TOKEN", "")
    if "influx" in selected_sinks and not token:
        raise ValueError("InfluxDB token is required via --influx-token or INFLUXDB_TOKEN.")
    sinks = []
    try:
        if "jsonl" in selected_sinks:
            sinks.append(JsonlSink(args.jsonl_out))
        if "influx" in selected_sinks:
            writer = InfluxWriter(args.influx_url, args.influx_org, args.influx_bucket, token)
            sinks.append(InfluxTelemetrySink(writer))
        if "mqtt" in selected_sinks:
            sinks.append(MqttTelemetrySink(args.mqtt_host, args.mqtt_port, args.mqtt_topic_prefix, args.mqtt_qos))
    except Exception:
        for sink in reversed(sinks):
            sink.close()
        raise
    stats = replay_telemetry(
        telemetry,
        FanoutSink(sinks),
        speed=args.speed,
        batch_size=args.batch_size,
        max_records=args.max_records,
    )
    print(
        f"Replayed {stats.records_sent} records in {stats.batches_sent} batches "
        f"({stats.source_duration_s:.3f}s source, {stats.elapsed_s:.3f}s elapsed)"
    )


def cmd_influx_write(args: argparse.Namespace) -> None:
    token = args.influx_token or os.environ.get("INFLUXDB_TOKEN", "")
    if not token:
        raise ValueError("InfluxDB token is required via --influx-token or INFLUXDB_TOKEN.")
    if args.batch_size < 1:
        raise ValueError("batch-size must be at least 1")
    writer = InfluxWriter(args.influx_url, args.influx_org, args.influx_bucket, token)
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    for start in range(0, len(lines), args.batch_size):
        writer.write_lines(lines[start : start + args.batch_size])
    print(f"Wrote {len(lines)} line-protocol records to InfluxDB bucket '{args.influx_bucket}'")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Industrial reliability and predictive-maintenance layer")
    parser.set_defaults(func=None)
    default_profile = PROJECT_ROOT / "config" / "asset_profile.json"

    sub = parser.add_subparsers(dest="command")

    simulate = sub.add_parser("simulate", help="Generate deterministic telemetry with seeded faults")
    simulate.add_argument("--profile", default=default_profile)
    simulate.add_argument("--duration-sec", type=float, default=1200.0)
    simulate.add_argument("--sampling-hz", type=float, default=None)
    simulate.add_argument("--seed", type=int, default=7)
    simulate.add_argument("--out", default=PROJECT_ROOT / "data" / "simulated" / "mixed_faults.csv")
    simulate.set_defaults(func=cmd_simulate)

    features = sub.add_parser("features", help="Extract rolling diagnostic features")
    features.add_argument("--profile", default=default_profile)
    features.add_argument("--input", required=True)
    features.add_argument("--out", required=True)
    features.add_argument("--sampling-hz", type=float, default=None)
    features.add_argument("--window-sec", type=float, default=5.0)
    features.add_argument("--step-sec", type=float, default=5.0)
    features.set_defaults(func=cmd_features)

    baseline = sub.add_parser("baseline", help="Fit robust healthy baseline")
    baseline.add_argument("--features", required=True)
    baseline.add_argument("--out", required=True)
    baseline.set_defaults(func=cmd_baseline)

    analyze = sub.add_parser("analyze", help="Score features, detect alerts, and write recommendations")
    analyze.add_argument("--features", required=True)
    analyze.add_argument("--baseline", required=True)
    analyze.add_argument("--out-dir", default=PROJECT_ROOT / "output" / "demo")
    analyze.set_defaults(func=cmd_analyze)

    report = sub.add_parser("report", help="Write Markdown report and static dashboard")
    report.add_argument("--out-dir", default=PROJECT_ROOT / "output" / "demo")
    report.add_argument("--report", default=PROJECT_ROOT / "reports" / "maintenance_case_report.md")
    report.add_argument("--dashboard", default=PROJECT_ROOT / "dashboard" / "index.html")
    report.set_defaults(func=cmd_report)

    demo = sub.add_parser("demo", help="Run the complete demonstration pipeline")
    demo.add_argument("--profile", default=default_profile)
    demo.add_argument("--duration-sec", type=float, default=1200.0)
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--telemetry", default=PROJECT_ROOT / "data" / "simulated" / "mixed_faults.csv")
    demo.add_argument("--out-dir", default=PROJECT_ROOT / "output" / "demo")
    demo.add_argument("--report", default=PROJECT_ROOT / "reports" / "maintenance_case_report.md")
    demo.add_argument("--dashboard", default=PROJECT_ROOT / "dashboard" / "index.html")
    demo.set_defaults(func=cmd_demo)

    replay = sub.add_parser("replay", help="Replay sample telemetry to JSONL, InfluxDB, or MQTT sinks")
    replay.add_argument("--input", default=PROJECT_ROOT / "data" / "simulated" / "mixed_faults.csv")
    replay.add_argument("--sink", action="append", choices=("jsonl", "influx", "mqtt"), default=[])
    replay.add_argument("--jsonl-out", default=PROJECT_ROOT / "output" / "replay" / "telemetry.jsonl")
    replay.add_argument("--speed", type=float, default=0.0, help="Replay multiplier; zero sends without waiting")
    replay.add_argument("--batch-size", type=int, default=25)
    replay.add_argument("--max-records", type=int, default=None)
    replay.add_argument("--influx-url", default="http://localhost:8086")
    replay.add_argument("--influx-org", default="portfolio")
    replay.add_argument("--influx-bucket", default="maintenance")
    replay.add_argument("--influx-token", default=None)
    replay.add_argument("--mqtt-host", default="localhost")
    replay.add_argument("--mqtt-port", type=int, default=1883)
    replay.add_argument("--mqtt-topic-prefix", default="factory/mhc")
    replay.add_argument("--mqtt-qos", type=int, choices=(0, 1, 2), default=1)
    replay.set_defaults(func=cmd_replay)

    influx_write = sub.add_parser("influx-write", help="Upload generated line protocol to InfluxDB")
    influx_write.add_argument("--input", default=PROJECT_ROOT / "output" / "demo" / "condition_windows.lp")
    influx_write.add_argument("--influx-url", default="http://localhost:8086")
    influx_write.add_argument("--influx-org", default="portfolio")
    influx_write.add_argument("--influx-bucket", default="maintenance")
    influx_write.add_argument("--influx-token", default=None)
    influx_write.add_argument("--batch-size", type=int, default=500)
    influx_write.set_defaults(func=cmd_influx_write)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.func is None:
        parser.print_help()
        return 2
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
