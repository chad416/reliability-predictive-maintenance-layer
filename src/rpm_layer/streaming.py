from __future__ import annotations

import json
import numbers
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Protocol
from urllib import parse, request

import pandas as pd


class TelemetrySink(Protocol):
    def write(self, records: list[dict[str, object]]) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class ReplayStats:
    records_sent: int
    batches_sent: int
    source_duration_s: float
    elapsed_s: float


def _escape_tag(value: object) -> str:
    return str(value).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def _field_value(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, numbers.Integral):
        return f"{value}i"
    if isinstance(value, numbers.Real):
        return repr(float(value))
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def telemetry_line_protocol(record: dict[str, object]) -> str:
    """Serialize one acquisition sample using the repository telemetry contract."""
    timestamp = pd.to_datetime(record["timestamp"], errors="raise")
    timestamp_ns = int(timestamp.value)
    tags = f"asset_id={_escape_tag(record.get('asset_id', 'unknown'))}"
    fields = []
    for name in ("speed_rpm", "load_pct", "vibration_g", "current_a", "temperature_c", "acoustic_db"):
        if name in record:
            encoded = _field_value(record[name])
            if encoded is not None:
                fields.append(f"{name}={encoded}")
    if not fields:
        raise ValueError("Telemetry record has no numeric measurement fields.")
    return f"telemetry,{tags} {','.join(fields)} {timestamp_ns}"


class JsonlSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8", newline="\n")

    def write(self, records: list[dict[str, object]]) -> None:
        for record in records:
            self._handle.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class InfluxWriter:
    def __init__(
        self,
        url: str,
        org: str,
        bucket: str,
        token: str,
        timeout_s: float = 10.0,
        retries: int = 3,
        opener: Callable[..., object] = request.urlopen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if retries < 1:
            raise ValueError("retries must be at least 1")
        query = parse.urlencode({"org": org, "bucket": bucket, "precision": "ns"})
        self.endpoint = f"{url.rstrip('/')}/api/v2/write?{query}"
        self.token = token
        self.timeout_s = timeout_s
        self.retries = retries
        self._opener = opener
        self._sleep = sleep

    def write_lines(self, lines: Iterable[str]) -> None:
        payload = "\n".join(line.rstrip("\n") for line in lines if line.strip()).encode("utf-8")
        if not payload:
            return
        outgoing = request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Token {self.token}",
                "Content-Type": "text/plain; charset=utf-8",
                "Accept": "application/json",
            },
        )
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self._opener(outgoing, timeout=self.timeout_s)
                close = getattr(response, "close", None)
                if close:
                    close()
                return
            except Exception as exc:  # Network failures are normalized after bounded retries.
                last_error = exc
                if attempt + 1 < self.retries:
                    self._sleep(0.25 * (2**attempt))
        raise RuntimeError(f"InfluxDB write failed after {self.retries} attempts: {last_error}") from last_error


class InfluxTelemetrySink:
    def __init__(self, writer: InfluxWriter) -> None:
        self.writer = writer

    def write(self, records: list[dict[str, object]]) -> None:
        self.writer.write_lines(telemetry_line_protocol(record) for record in records)

    def close(self) -> None:
        return None


class MqttTelemetrySink:
    def __init__(self, host: str, port: int, topic_prefix: str, qos: int = 1) -> None:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError("MQTT publishing requires the optional 'mqtt' dependency.") from exc
        self._mqtt = mqtt
        self._client = None
        self._host = host
        self._port = port
        self._topic_prefix = topic_prefix.strip("/")
        self._qos = qos

    def _ensure_connected(self) -> None:
        if self._client is not None:
            return
        client = self._mqtt.Client(self._mqtt.CallbackAPIVersion.VERSION2)
        client.connect(self._host, self._port, keepalive=30)
        client.loop_start()
        self._client = client

    def write(self, records: list[dict[str, object]]) -> None:
        self._ensure_connected()
        assert self._client is not None
        try:
            for record in records:
                asset_id = str(record.get("asset_id", "unknown"))
                topic = f"{self._topic_prefix}/{asset_id}/telemetry"
                result = self._client.publish(topic, json.dumps(record, default=str), qos=self._qos)
                result.wait_for_publish(timeout=10.0)
                if result.rc != 0:
                    raise RuntimeError(f"MQTT publish failed with result code {result.rc}")
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None


class FanoutSink:
    def __init__(self, sinks: list[TelemetrySink]) -> None:
        if not sinks:
            raise ValueError("At least one telemetry sink is required.")
        self.sinks = sinks

    def write(self, records: list[dict[str, object]]) -> None:
        for sink in self.sinks:
            sink.write(records)

    def close(self) -> None:
        errors = []
        for sink in reversed(self.sinks):
            try:
                sink.close()
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise RuntimeError(f"Failed to close {len(errors)} telemetry sink(s).") from errors[0]


def replay_telemetry(
    telemetry: pd.DataFrame,
    sink: TelemetrySink,
    speed: float = 1.0,
    batch_size: int = 25,
    max_records: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> ReplayStats:
    """Replay timestamped telemetry with deterministic pacing and bounded batches.

    A speed of zero disables waiting and is intended for commissioning smoke tests.
    """
    wall_start = monotonic()
    try:
        if speed < 0:
            raise ValueError("speed must be zero or positive")
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if max_records is not None and max_records < 0:
            raise ValueError("max_records must be zero or positive")
        if "timestamp" not in telemetry:
            raise ValueError("Telemetry input must contain a timestamp column.")

        working = telemetry.head(max_records) if max_records is not None else telemetry
        if working.empty:
            return ReplayStats(0, 0, 0.0, round(monotonic() - wall_start, 6))
        timestamps = pd.to_datetime(working["timestamp"], errors="coerce", format="mixed")
        if timestamps.isna().any():
            raise ValueError("Telemetry input contains invalid timestamps.")
        if not timestamps.is_monotonic_increasing:
            raise ValueError("Telemetry timestamps must be monotonic increasing.")

        records = working.to_dict(orient="records")
        source_start = timestamps.iloc[0]
        source_duration = float((timestamps.iloc[-1] - source_start).total_seconds())
        batches = 0
        buffer: list[dict[str, object]] = []
        for index, record in enumerate(records):
            if speed > 0:
                target_elapsed = float((timestamps.iloc[index] - source_start).total_seconds()) / speed
                remaining = target_elapsed - (monotonic() - wall_start)
                if remaining > 0:
                    sleep(remaining)
            buffer.append(record)
            if len(buffer) >= batch_size:
                sink.write(buffer)
                batches += 1
                buffer = []
        if buffer:
            sink.write(buffer)
            batches += 1
        return ReplayStats(len(records), batches, source_duration, round(monotonic() - wall_start, 6))
    finally:
        sink.close()
