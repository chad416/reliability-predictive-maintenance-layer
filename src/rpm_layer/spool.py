from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from rpm_layer.streaming import TelemetrySink


@dataclass(frozen=True)
class SpoolItem:
    item_id: int
    records: list[dict[str, object]]
    attempts: int


class SpoolFullError(RuntimeError):
    pass


class SqliteSpool:
    """Durable FIFO outbox for telemetry batches awaiting remote delivery."""

    def __init__(self, path: str | Path, max_batches: int = 100_000) -> None:
        if max_batches < 1:
            raise ValueError("max_batches must be at least 1")
        self.path = Path(path)
        self.max_batches = max_batches
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT
            )
            """
        )
        self._connection.commit()

    def enqueue(self, records: list[dict[str, object]]) -> int:
        if not records:
            raise ValueError("Cannot enqueue an empty telemetry batch.")
        payload = json.dumps(records, separators=(",", ":"), default=str, allow_nan=False)
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            row = self._connection.execute("SELECT COUNT(*) FROM telemetry_outbox").fetchone()
            if int(row[0]) >= self.max_batches:
                raise SpoolFullError(f"Telemetry spool reached its {self.max_batches}-batch capacity.")
            cursor = self._connection.execute(
                "INSERT INTO telemetry_outbox (created_at, payload) VALUES (?, ?)",
                (created_at, payload),
            )
            self._connection.commit()
            return int(cursor.lastrowid)
        except Exception:
            if self._connection.in_transaction:
                self._connection.rollback()
            raise

    def pending(self, limit: int = 100) -> list[SpoolItem]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        rows = self._connection.execute(
            "SELECT id, payload, attempts FROM telemetry_outbox ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        return [SpoolItem(int(row[0]), json.loads(row[1]), int(row[2])) for row in rows]

    def acknowledge(self, item_id: int) -> None:
        self._connection.execute("DELETE FROM telemetry_outbox WHERE id = ?", (item_id,))
        self._connection.commit()

    def record_failure(self, item_id: int, error: Exception) -> None:
        message = str(error)[:1000]
        self._connection.execute(
            "UPDATE telemetry_outbox SET attempts = attempts + 1, last_error = ? WHERE id = ?",
            (message, item_id),
        )
        self._connection.commit()

    def count(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) FROM telemetry_outbox").fetchone()
        return int(row[0])

    def close(self) -> None:
        self._connection.close()


class StoreAndForwardSink:
    """Persist before delivery and retain failed batches for a later drain."""

    def __init__(
        self,
        downstream: TelemetrySink,
        spool_path: str | Path,
        retry_interval_s: float = 30.0,
        max_batches: int = 100_000,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if retry_interval_s < 0:
            raise ValueError("retry_interval_s must be zero or positive")
        self.downstream = downstream
        self.spool = SqliteSpool(spool_path, max_batches=max_batches)
        self.retry_interval_s = retry_interval_s
        self._monotonic = monotonic
        self._retry_after = 0.0
        self.pending_after_close = 0

    def write(self, records: list[dict[str, object]]) -> None:
        self.spool.enqueue(records)
        if self._monotonic() >= self._retry_after:
            self.flush(raise_on_error=False)

    def flush(self, limit: int = 100, raise_on_error: bool = False) -> int:
        delivered_records = 0
        for item in self.spool.pending(limit):
            try:
                self.downstream.write(item.records)
            except Exception as exc:
                self.spool.record_failure(item.item_id, exc)
                self._retry_after = self._monotonic() + self.retry_interval_s
                if raise_on_error:
                    raise RuntimeError(f"Failed to drain spool item {item.item_id}: {exc}") from exc
                break
            self.spool.acknowledge(item.item_id)
            delivered_records += len(item.records)
        return delivered_records

    def close(self) -> None:
        self.pending_after_close = self.spool.count()
        try:
            self.downstream.close()
        finally:
            self.spool.close()


def drain_spool(path: str | Path, downstream: TelemetrySink, limit: int = 1000) -> tuple[int, int]:
    sink = StoreAndForwardSink(downstream, path)
    try:
        delivered = sink.flush(limit=limit, raise_on_error=True)
        remaining = sink.spool.count()
        return delivered, remaining
    finally:
        sink.close()
