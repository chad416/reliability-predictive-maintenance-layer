from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records"))


def write_dashboard(
    scored_features: pd.DataFrame,
    alerts: pd.DataFrame,
    recommendations: pd.DataFrame,
    path: str | Path,
    validation_summary: pd.DataFrame | None = None,
    validation_metrics: dict | None = None,
    quality_metrics: dict | None = None,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scored": _records(scored_features),
        "alerts": _records(alerts),
        "recommendations": _records(recommendations),
        "validationSummary": _records(validation_summary) if validation_summary is not None else [],
        "validationMetrics": validation_metrics or {},
        "qualityMetrics": quality_metrics or {},
    }
    title = "Reliability and Predictive Maintenance Layer"
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18202a;
      --muted: #5b6472;
      --line: #d7dde6;
      --panel: #f7f8fb;
      --accent: #136f63;
      --warn: #b7791f;
      --crit: #b42318;
      --ok: #287d3c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    header {{
      padding: 28px 36px 18px;
      border-bottom: 1px solid var(--line);
      background: #f3f6f9;
    }}
    .header-meta {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 14px; }}
    .status {{ display: inline-block; border-radius: 999px; padding: 6px 10px; background: #e6f4ef; color: #116149; font-size: 11px; font-weight: 700; letter-spacing: .08em; }}
    .scope {{ color: var(--muted); font-size: 12px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }}
    p {{ color: var(--muted); margin: 0; line-height: 1.45; }}
    main {{ padding: 24px 36px 40px; display: grid; gap: 22px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap: 12px; }}
    .kpi {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fff; min-height: 92px; }}
    .kpi span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .kpi strong {{ display: block; font-size: 28px; margin-top: 8px; }}
    section {{ border-top: 1px solid var(--line); padding-top: 20px; }}
    .chart {{ width: 100%; min-height: 260px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); padding: 12px; }}
    svg {{ width: 100%; height: 240px; display: block; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 10px 8px; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; background: #f7f8fb; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 3px 9px; color: #fff; font-size: 12px; }}
    .critical {{ background: var(--crit); }}
    .warning {{ background: var(--warn); }}
    .advisory {{ background: var(--accent); }}
    .normal {{ background: var(--ok); }}
    .system-map {{ border: 1px solid var(--line); border-radius: 8px; padding: 18px; background: linear-gradient(135deg, #f7fbfa, #f6f8fb); }}
    .map-flow {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; align-items: stretch; }}
    .map-node {{ position: relative; border: 1px solid #b9d5cf; border-radius: 8px; padding: 14px 12px; background: #fff; min-height: 88px; font-weight: 700; color: var(--ink); }}
    .map-node:not(:last-child)::after {{ content: "→"; position: absolute; right: -18px; top: 32px; color: var(--accent); font-size: 20px; font-weight: 700; z-index: 1; }}
    .map-node span {{ display: block; color: var(--muted); font-size: 11px; font-weight: 400; line-height: 1.35; margin-top: 7px; }}
    .system-note {{ margin-top: 12px; font-size: 12px; }}
    @media (max-width: 820px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .kpis {{ grid-template-columns: repeat(2, minmax(130px, 1fr)); }}
      table {{ font-size: 12px; }}
      .map-flow {{ grid-template-columns: 1fr; }}
      .map-node:not(:last-child)::after {{ content: "↓"; right: 50%; top: auto; bottom: -21px; transform: translateX(50%); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <p>Condition monitoring, explainable diagnostics, and maintenance recommendations for an industrial drive axis.</p>
    <div class="header-meta"><span class="status">SOFTWARE-READY / HARDWARE PHASE 2</span><span class="scope">Simulation, validation, and OT/IT integration are complete; physical sensor commissioning is the next gate.</span></div>
  </header>
  <main>
    <div class="kpis" id="kpis"></div>
    <section class="system-map">
      <h2>Reliability loop</h2>
      <div class="map-flow" role="img" aria-label="Telemetry flows through quality, features, diagnostics, and maintenance actions">
        <div class="map-node">Telemetry<span>vibration · current · temperature · speed · load</span></div>
        <div class="map-node">Quality gate<span>sampling · gaps · nulls · ranges</span></div>
        <div class="map-node">Feature window<span>RMS · FFT · kurtosis · thermal slope</span></div>
        <div class="map-node">Evidence rule<span>median/IQR deviation + severity</span></div>
        <div class="map-node">Maintenance action<span>inspection · spares · verification</span></div>
      </div>
      <p class="system-note">The same contract can be fed by OPC UA, MQTT, or local DAQ adapters; the analytics and maintenance handoff remain unchanged.</p>
    </section>
    <section>
      <h2>Condition Index Timeline</h2>
      <div class="chart"><svg id="conditionChart" role="img" aria-label="Condition index timeline"></svg></div>
    </section>
    <section>
      <h2>Alert Episodes</h2>
      <table id="alertsTable"></table>
    </section>
    <section>
      <h2>Maintenance Recommendations</h2>
      <table id="recommendationsTable"></table>
    </section>
    <section>
      <h2>Validation Evidence</h2>
      <table id="validationTable"></table>
    </section>
  </main>
  <script>
    const data = {json.dumps(payload)};
    const severityRank = {{ normal: 0, advisory: 1, warning: 2, critical: 3 }};

    function renderKpis() {{
      const scored = data.scored;
      const alerts = data.alerts;
      const maxCondition = Math.max(...scored.map(d => Number(d.condition_index || 0)));
      const critical = alerts.filter(d => d.severity === "critical").length;
      const warning = alerts.filter(d => d.severity === "warning").length;
      const diagnoses = new Set(alerts.map(d => d.diagnosis));
      const metrics = data.validationMetrics || {{}};
      const quality = data.qualityMetrics || {{}};
      const items = [
        ["Windows", scored.length],
        ["Max condition", maxCondition.toFixed(1) + "/100"],
        ["Data quality", quality.status || "n/a"],
        ["Warning/Critical", warning + "/" + critical],
        ["Fault recall", Number(metrics.fault_window_recall_pct || 0).toFixed(1) + "%"],
        ["Healthy false alerts", Number(metrics.healthy_false_alert_rate_pct || 0).toFixed(1) + "%"],
        ["Diagnoses", diagnoses.size]
      ];
      document.getElementById("kpis").innerHTML = items.map(([label, value]) =>
        `<div class="kpi"><span>${{label}}</span><strong>${{value}}</strong></div>`
      ).join("");
    }}

    function renderChart() {{
      const scored = data.scored;
      const svg = document.getElementById("conditionChart");
      const width = 1000;
      const height = 240;
      const pad = 28;
      svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
      const values = scored.map(d => Number(d.condition_index || 0));
      const maxY = Math.max(100, ...values);
      const points = values.map((value, index) => {{
        const x = pad + index * ((width - pad * 2) / Math.max(values.length - 1, 1));
        const y = height - pad - (value / maxY) * (height - pad * 2);
        return [x, y];
      }});
      const path = points.map((p, i) => `${{i === 0 ? "M" : "L"}} ${{p[0].toFixed(2)}} ${{p[1].toFixed(2)}}`).join(" ");
      const alertMarks = data.alerts.slice(0, 80).map(alert => {{
        const idx = scored.findIndex(row => row.window_start === alert.window_start);
        if (idx < 0) return "";
        const point = points[idx];
        return `<circle cx="${{point[0]}}" cy="${{point[1]}}" r="4" fill="${{alert.severity === "critical" ? "#b42318" : "#b7791f"}}" />`;
      }}).join("");
      svg.innerHTML = `
        <line x1="${{pad}}" y1="${{height-pad}}" x2="${{width-pad}}" y2="${{height-pad}}" stroke="#9aa4b2"/>
        <line x1="${{pad}}" y1="${{pad}}" x2="${{pad}}" y2="${{height-pad}}" stroke="#9aa4b2"/>
        <line x1="${{pad}}" y1="${{height-pad-0.7*(height-pad*2)}}" x2="${{width-pad}}" y2="${{height-pad-0.7*(height-pad*2)}}" stroke="#b42318" stroke-dasharray="6 6"/>
        <path d="${{path}}" fill="none" stroke="#136f63" stroke-width="3"/>
        ${{alertMarks}}
        <text x="${{pad}}" y="18" fill="#5b6472" font-size="13">Condition index</text>
      `;
    }}

    function table(targetId, columns, rows) {{
      const target = document.getElementById(targetId);
      const head = `<tr>${{columns.map(c => `<th>${{c.label}}</th>`).join("")}}</tr>`;
      const body = rows.map(row => `<tr>${{columns.map(c => `<td>${{c.render ? c.render(row[c.key], row) : (row[c.key] ?? "")}}</td>`).join("")}}</tr>`).join("");
      target.innerHTML = head + body;
    }}

    renderKpis();
    renderChart();
    table("alertsTable", [
      {{ key: "severity", label: "Severity", render: value => `<span class="badge ${{value}}">${{value}}</span>` }},
      {{ key: "diagnosis", label: "Diagnosis" }},
      {{ key: "window_start", label: "Start" }},
      {{ key: "condition_index", label: "Condition" }},
      {{ key: "evidence", label: "Evidence" }}
    ], data.alerts.slice(0, 24));
    table("recommendationsTable", [
      {{ key: "priority", label: "Priority" }},
      {{ key: "diagnosis", label: "Diagnosis" }},
      {{ key: "downtime_class", label: "Downtime" }},
      {{ key: "recommended_action", label: "Action" }},
      {{ key: "verification", label: "Verification" }}
    ], data.recommendations);
    table("validationTable", [
      {{ key: "validation_label", label: "Seeded condition" }},
      {{ key: "expected_diagnosis", label: "Expected" }},
      {{ key: "windows", label: "Windows" }},
      {{ key: "detected_windows", label: "Detected" }},
      {{ key: "detection_rate_pct", label: "Detection %" }},
      {{ key: "detection_delay_s", label: "Delay s" }}
    ], data.validationSummary);
  </script>
</body>
</html>
"""
    target.write_text(html_doc, encoding="utf-8")
