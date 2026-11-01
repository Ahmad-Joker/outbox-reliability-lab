"""HTTP API and read-only status dashboard. No worker actions exposed publicly."""
from __future__ import annotations

import os
from html import escape
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .service import IdempotencyConflict, InputError, OutboxService


class OrderRequest(BaseModel):
    amount_cents: int = Field(gt=0, le=1_000_000_000, strict=True)


def create_app(db_path: str | Path | None = None) -> FastAPI:
    service = OutboxService(db_path or os.environ.get("OUTBOX_DB", "outbox.db"))
    app = FastAPI(title="Outbox Reliability Lab", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "storage": "sqlite"}

    @app.post("/orders", status_code=201)
    def create_order(payload: OrderRequest, idempotency_key: str | None = Header(default=None)) -> dict:
        if idempotency_key is None:
            raise HTTPException(status_code=400, detail="Idempotency-Key header required")
        try:
            result = service.create_order(payload.amount_cents, idempotency_key)
        except InputError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return result

    @app.get("/orders/{order_id}")
    def order(order_id: str) -> dict:
        result = service.get_order(order_id)
        if result is None:
            raise HTTPException(status_code=404, detail="order not found")
        return result

    @app.get("/events")
    def events() -> list[dict]:
        return service.list_events()

    @app.get("/events/{event_id}/audit")
    def audit(event_id: str) -> list[dict]:
        return service.audit(event_id)

    @app.get("/stats")
    def stats() -> dict:
        return service.stats()

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard() -> str:
        rows = "".join(
            f"<tr><td>{escape(e['id'][:8])}</td><td>{escape(e['status'])}</td><td>{e['attempts']}</td><td>{escape(e['last_error'] or '-')}</td></tr>"
            for e in service.list_events()
        )
        s = service.stats()
        return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Outbox Reliability Lab</title><style>body{{font:16px system-ui;margin:2rem auto;max-width:960px;padding:0 1rem;background:#f8fafc;color:#17253c}}h1{{color:#12466b}}.metric{{display:inline-block;background:white;padding:1rem 1.5rem;margin:.4rem;border:1px solid #d8e1eb;border-radius:10px}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{text-align:left;padding:.8rem;border-bottom:1px solid #e2e8f0}}code{{font-size:.9rem}}</style></head><body><h1>Outbox Reliability Lab</h1><p>Local educational simulation · No real payments or external delivery</p><div class="metric"><b>Orders</b><p>{s['orders']}</p></div><div class="metric"><b>Deliveries</b><p>{s['deliveries']}</p></div><div class="metric"><b>Audit entries</b><p>{s['audit_records']}</p></div><h2>Outbox events</h2><table><thead><tr><th>Event</th><th>Status</th><th>Attempts</th><th>Last error</th></tr></thead><tbody>{rows}</tbody></table><p>Use <code>python -m outbox_lab.cli --help</code> to inject failures. API docs: <a href="/docs">/docs</a></p></body></html>"""

    return app


app = create_app()
