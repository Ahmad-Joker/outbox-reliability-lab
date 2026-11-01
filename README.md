# Outbox Reliability Lab

**A local, fault-injectable transactional-outbox and idempotent-consumer teaching project.** Built to demonstrate backend reliability skills in real internship descriptions, not to process real money.

## What it does

A client creates a simulated order. The API writes the order **and** an outbox event in one SQLite transaction. A separate worker polls due events and delivers each to a simulated downstream inbox. It retries temporary failures with exponential backoff, dead-letters repeated failures, and recovers a crashed worker after its lease expires. The downstream inbox uses a unique event ID to prevent duplicate side effects on redelivery.

```
POST /orders  ->  SQLite [orders + outbox]  ->  worker claim/lease
                                                      |
                                                inject failure
                                                      |
                                  simulated inbox [UNIQUE event_id]
                                                      |
                                       ack / retry / dead letter
                                                      |
                                        GET /dashboard + audit
```

This is **at-least-once processing with an idempotent simulated recipient**, not a claim of exactly-once external delivery. SQLite represents both local and simulated downstream state in the same database file. A production system would use separate services, a real broker, authentication, secrets management and operational controls.

## Install and run

Requires Python 3.11+ and pip. No API key, cloud account or paid service.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
outbox-lab --db demo.sqlite init
outbox-lab --db demo.sqlite demo
outbox-lab --db demo.sqlite stats
python -m pytest -q
```

To use the API, open a separate terminal:

```bash
OUTBOX_DB=demo.sqlite uvicorn outbox_lab.api:app --reload
# Windows PowerShell: $env:OUTBOX_DB="demo.sqlite"; uvicorn outbox_lab.api:app --reload
curl -X POST http://127.0.0.1:8000/orders -H 'Content-Type: application/json' -H 'Idempotency-Key: sample-001' -d '{"amount_cents":1250}'
outbox-lab --db demo.sqlite worker
```

Open `http://127.0.0.1:8000/dashboard` and `http://127.0.0.1:8000/docs`.

**API endpoints:** `POST /orders`, `GET /orders/{id}`, `GET /events`, `GET /events/{id}/audit`, `GET /stats`, `GET /health`, `GET /dashboard`. The API does not expose worker control, so failures are injected locally through CLI.

### Reproduce failures

```bash
outbox-lab --db retry.sqlite submit --amount 1200 --key failure-case
outbox-lab --db retry.sqlite worker --failure before   # becomes retry
# Wait one second for backoff, then:
outbox-lab --db retry.sqlite worker                  # becomes delivered

outbox-lab --db crash.sqlite submit --amount 2200 --key crash-case
outbox-lab --db crash.sqlite worker --failure after   # side effect committed; no ack
# Wait 30 seconds for lease expiry, then:
outbox-lab --db crash.sqlite recover
outbox-lab --db crash.sqlite worker                  # duplicate suppressed
outbox-lab --db crash.sqlite stats
```

The `demo` command advances a deterministic simulated clock for fault cases, so you can see both failure modes without waiting. It writes synthetic orders to the specified DB. For production, never use the demo command.

### Docker (optional, not required)

```bash
docker compose up --build
```

This starts an API and a worker sharing a persistent SQLite volume. Docker execution is not verified unless explicitly recorded in `docs/VERIFICATION.md`.

## How to explain the design

1. The **transactional outbox** avoids a lost-event gap between saving an order and creating its notification event.
2. The **polling worker** claims a due event with an SQLite `BEGIN IMMEDIATE` transaction, giving it a time-limited lease.
3. A **retry** has bounded exponential backoff. After `max_attempts` (default 3), the event becomes `dead` for operator review.
4. The **idempotent inbox** records `event_id` as a unique key. Replaying an event cannot create a second simulated delivery.
5. The **audit log** records queued, claimed, retry, recovered and delivered/dead transitions.

## Files

- `src/outbox_lab/db.py` — schema, WAL, SQLite connection setup.
- `src/outbox_lab/service.py` — atomic writes, leases, worker processing, retry, recovery, audit and stats.
- `src/outbox_lab/api.py` — validated HTTP endpoints and read-only HTML dashboard.
- `src/outbox_lab/cli.py` — local worker, demo, fault injection and inspection.
- `tests/` — rollback, idempotency, concurrent claims, retries, crash recovery, dead-letter and HTTP smoke tests.
- `MASTER_PROMPT.md` — pre-code implementation contract.
- `docs/RESEARCH.md` — dated employer evidence, competing solutions and ranking.
- `docs/VERIFICATION.md` — actual local verification, limitations and GitHub status.

## Security and limitations

Local educational MVP. No authentication, tenant separation, external broker, payment processing, external side effects, real network failure simulation or production deployment. No true multi-node/distributed guarantee. SQLite supports this demo, not a replacement for Kafka, Temporal or a production transactional outbox service. `--failure after` simulates a crash by deliberately leaving a processing lease unacknowledged; it does not kill the OS process. The UI is a read-only snapshot, not live telemetry. No real customer data is used.

## Hiring relevance

Official job descriptions reviewed 2026-11-01: [Monzo intern](https://job-boards.greenhouse.io/monzo/jobs/8156261), [Amazon ML SDE intern](https://www.amazon.jobs/en/jobs/10588762/2027-software-dev-engineer-intern-machine-learning-uk), [Cloudflare intern](https://job-boards.greenhouse.io/cloudflare/jobs/8245211), [Graphcore platform intern](https://job-boards.greenhouse.io/graphcore/jobs/8894965002), [Aleph Cairo automation](https://jobs.lever.co/aleph/f6da715d-f67e-4c25-bab1-b2e5d14709d0). This project proves Python, SQL, transactions, idempotency, API design, concurrency tests, CI and debugging; it does **not** prove Go, Kafka, Kubernetes, cloud deployment or ML training.

**Truthful CV bullet (once local verification passes):** "Built a Python/FastAPI and SQLite transactional-outbox lab with idempotent event consumption, leased worker recovery, bounded retries, failure injection, automated tests and an audit dashboard; verified crash-after-delivery recovery without duplicate simulated side effects."
