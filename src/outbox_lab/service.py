"""Transactional outbox, leased polling, retry and idempotent inbox semantics."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .db import connect, initialize


class InputError(ValueError):
    pass


class IdempotencyConflict(ValueError):
    pass


def utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


class OutboxService:
    def __init__(self, path: str | Path, *, max_attempts: int = 3, lease_seconds: int = 30):
        if max_attempts < 1 or lease_seconds < 1:
            raise ValueError("max_attempts and lease_seconds must be positive")
        self.path = str(path)
        self.max_attempts = max_attempts
        self.lease_seconds = lease_seconds
        initialize(path)

    def create_order(self, amount_cents: int, idempotency_key: str, *, now: float | None = None) -> dict[str, Any]:
        if type(amount_cents) is not int or not 1 <= amount_cents <= 1_000_000_000:
            raise InputError("amount_cents must be an integer between 1 and 1000000000")
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 128 or not idempotency_key.strip():
            raise InputError("Idempotency-Key must be 1–128 nonblank characters")
        now = time.time() if now is None else now
        with connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                old = conn.execute("SELECT id,amount_cents FROM orders WHERE idempotency_key=?", (idempotency_key,)).fetchone()
                if old:
                    if old["amount_cents"] != amount_cents:
                        raise IdempotencyConflict("idempotency key already used for a different amount")
                    conn.execute("COMMIT")
                    return {"order_id": old["id"], "created": False}
                order_id, event_id = str(uuid.uuid4()), str(uuid.uuid4())
                payload = json.dumps({"order_id": order_id, "amount_cents": amount_cents}, sort_keys=True)
                conn.execute("INSERT INTO orders VALUES (?,?,?,?)", (order_id, idempotency_key, amount_cents, now))
                conn.execute("INSERT INTO outbox (id,order_id,event_type,payload,status,next_attempt_at,created_at) VALUES (?,?,?,?,?,?,?)",
                             (event_id, order_id, "OrderCreated", payload, "queued", now, now))
                self._audit(conn, event_id, "queued", "order and event committed atomically", now)
                conn.execute("COMMIT")
                return {"order_id": order_id, "event_id": event_id, "created": True}
            except Exception:
                conn.execute("ROLLBACK")
                raise

    @staticmethod
    def _audit(conn: sqlite3.Connection, event_id: str, action: str, detail: str, now: float) -> None:
        conn.execute("INSERT INTO audit(event_id,action,detail,at) VALUES (?,?,?,?)", (event_id, action, detail[:500], now))

    def claim(self, *, now: float | None = None) -> dict[str, Any] | None:
        now = time.time() if now is None else now
        with connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute("SELECT * FROM outbox WHERE status IN ('queued','retry') AND next_attempt_at<=? ORDER BY created_at,id LIMIT 1", (now,)).fetchone()
                if row is None:
                    conn.execute("COMMIT")
                    return None
                conn.execute("UPDATE outbox SET status='processing',attempts=attempts+1,lease_until=? WHERE id=?", (now+self.lease_seconds, row["id"]))
                self._audit(conn, row["id"], "claimed", f"attempt {row['attempts']+1}", now)
                conn.execute("COMMIT")
                return {**dict(row), "attempts": row["attempts"]+1}
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def _deliver(self, row: dict[str, Any], now: float) -> bool:
        # A second, separately committed transaction models a downstream inbox.
        # This is NOT a real remote service and does not imply end-to-end exactly-once delivery.
        with connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("INSERT OR IGNORE INTO deliveries(event_id,order_id,payload,delivered_at) VALUES (?,?,?,?)",
                               (row["id"], row["order_id"], row["payload"], now))
            conn.execute("COMMIT")
            return cur.rowcount == 1

    def _finish(self, row: dict[str, Any], *, now: float, error: str | None = None, new_delivery: bool = False) -> dict[str, Any]:
        with connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            if error is None:
                conn.execute("UPDATE outbox SET status='delivered',delivered_at=?,lease_until=NULL,last_error=NULL WHERE id=?", (now, row["id"]))
                action, detail = "delivered", "new downstream effect" if new_delivery else "duplicate suppressed by inbox"
            else:
                dead = row["attempts"] >= self.max_attempts
                status = "dead" if dead else "retry"
                delay = min(2 ** (row["attempts"]-1), 60)
                conn.execute("UPDATE outbox SET status=?,next_attempt_at=?,lease_until=NULL,last_error=? WHERE id=?",
                             (status, now+delay, error[:500], row["id"]))
                action, detail = status, error
            self._audit(conn, row["id"], action, detail, now)
            conn.execute("COMMIT")
            return {"event_id": row["id"], "outcome": action, "attempt": row["attempts"], "new_delivery": new_delivery}

    def process_one(self, *, failure: str = "none", now: float | None = None) -> dict[str, Any] | None:
        if failure not in ("none", "before", "after"):
            raise InputError("failure must be none, before or after")
        now = time.time() if now is None else now
        row = self.claim(now=now)
        if row is None:
            return None
        if failure == "before":
            return self._finish(row, now=now, error="injected failure before delivery")
        try:
            fresh = self._deliver(row, now)
        except Exception as exc:
            return self._finish(row, now=now, error=f"delivery failure: {type(exc).__name__}")
        if failure == "after":
            # Simulate process termination after the side effect, before ack.
            # The event stays processing until the lease expires and is recovered.
            return {"event_id": row["id"], "outcome": "simulated_crash_after_delivery", "attempt": row["attempts"], "new_delivery": fresh}
        return self._finish(row, now=now, new_delivery=fresh)

    def recover_stale(self, *, now: float | None = None) -> int:
        now = time.time() if now is None else now
        with connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute("SELECT id,attempts FROM outbox WHERE status='processing' AND lease_until<=?", (now,)).fetchall()
            for row in rows:
                dead = row["attempts"] >= self.max_attempts
                conn.execute("UPDATE outbox SET status=?,next_attempt_at=?,lease_until=NULL,last_error=? WHERE id=?",
                             ("dead" if dead else "retry", now, "worker lease expired", row["id"]))
                self._audit(conn, row["id"], "dead" if dead else "recovered", "expired worker lease", now)
            conn.execute("COMMIT")
            return len(rows)

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        with connect(self.path) as conn:
            row = conn.execute("SELECT o.id,o.amount_cents,o.created_at,e.id event_id,e.status,e.attempts,e.last_error FROM orders o JOIN outbox e ON e.order_id=o.id WHERE o.id=?", (order_id,)).fetchone()
            return {**dict(row), "created_at": utc(row["created_at"])} if row else None

    def list_events(self) -> list[dict[str, Any]]:
        with connect(self.path) as conn:
            return [dict(r) for r in conn.execute("SELECT id,order_id,status,attempts,last_error,next_attempt_at,lease_until FROM outbox ORDER BY created_at,id")]

    def audit(self, event_id: str) -> list[dict[str, Any]]:
        with connect(self.path) as conn:
            return [{**dict(r), "at": utc(r["at"])} for r in conn.execute("SELECT action,detail,at FROM audit WHERE event_id=? ORDER BY id", (event_id,))]

    def stats(self) -> dict[str, Any]:
        with connect(self.path) as conn:
            statuses = {r["status"]: r["n"] for r in conn.execute("SELECT status,COUNT(*) n FROM outbox GROUP BY status")}
            return {
                "orders": conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
                "deliveries": conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0],
                "events": statuses,
                "audit_records": conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0],
            }
