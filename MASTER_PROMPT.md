# MASTER PROMPT — Outbox Reliability Lab

Created 2026-11-01, before implementation. This is the implementation contract for this run.

## Problem, audience, evidence
Build a locally runnable reliability laboratory for student backend engineers, fintech software interns and technical interviewers. A database write followed by an asynchronous side effect can lose an event when a process crashes. At-least-once processing can deliver duplicates. Demonstrate a transactional outbox, retry/backoff, dead-letter state, leased worker recovery, an idempotent inbox and transparent evidence of injected failures. This is an educational MVP, not a bank, broker or production payment system.

Official hiring evidence checked 2026-11-01: Monzo 2027 Software Engineer Intern (Go, Kafka, Docker, testing): https://job-boards.greenhouse.io/monzo/jobs/8156261 ; Amazon 2027 ML SDE Intern (reliable distributed services, tests, AI-generated code verification): https://www.amazon.jobs/en/jobs/10588762/2027-software-dev-engineer-intern-machine-learning-uk ; Cloudflare 2027 SWE Intern (Go/Python, infrastructure): https://job-boards.greenhouse.io/cloudflare/jobs/8245211 ; Graphcore Cloud Platform Intern (Linux, scripting, CI, monitoring): https://job-boards.greenhouse.io/graphcore/jobs/8894965002 ; Aleph Cairo automation: https://jobs.lever.co/aleph/f6da715d-f67e-4c25-bab1-b2e5d14709d0 . Technical pattern references: https://microservices.io/patterns/communication-style/idempotent-consumer.html and https://microservices.io/patterns/data/polling-publisher.html . Existing more capable alternatives: Temporal (https://docs.temporal.io/design-patterns), Kafka, Celery. This project differentiates through a tiny local, inspectable failure-injection laboratory, not superior scalability.

## Ranking and decision
Weighted editorial scoring: hiring 25%, portfolio gap 20%, usefulness 15%, differentiation 15%, feasibility 15%, zero-cost 10%; each dimension scored 0–5. Outbox Reliability Lab (5,5,5,4,5,5) = 97/100; ReconcileAudit (4,4,5,3,5,5) = 85/100; SearchRankBench (5,4,4,4,3,4) = 82/100; EdgeVisionOps (4,4,4,5,2,3) = 75/100. Scores are editorial, not hiring probabilities. Avoid duplicate work with existing SolutionForge, AgentArena, DataPilot, HireReady, AgentShield and ReplayCI. Winner is a focused reliability service rather than another agent evaluator or CV-scoring app.

## Objective and MVP boundary
Build one independently runnable Python 3.11+ repository with SQLite persistence, FastAPI endpoints, a separate polling worker, CLI demo and tests. No real payments, external email, Kafka, real network message delivery, cloud deployment, paid services, LLM inference or actual multi-node distributed guarantees. No Docker daemon required for local verification; provide a Dockerfile/compose as an unverified optional path if Docker unavailable.

## User stories
1. A caller POSTs an order with positive integer amount_cents and Idempotency-Key. API atomically stores order and pending event; retrying same request returns same order without duplicate; conflicting payload returns HTTP 409.
2. A worker polls due events and records a simulated downstream delivery once, marking event delivered.
3. An operator can inject failure before delivery, observe retry/backoff, then successfully retry.
4. An operator can simulate a crash after delivery but before acknowledgement, recover expired leases and verify no duplicate downstream effect.
5. Repeated failures eventually enter a dead-letter state with audit history.
6. A reviewer can inspect status, event audit, stats, health and an HTML dashboard.

## Architecture and flow
Client -> FastAPI -> SQLite transaction [orders + outbox]. Separate CLI worker -> claim due outbox row with BEGIN IMMEDIATE and lease -> simulated downstream inbox with UNIQUE(event_id) -> ack delivered. If failure before inbox, schedule retry with exponential backoff. If simulated crash after inbox commit, leave lease; recover stale claims and redeliver; inbox unique key prevents duplicate effect. Events, deliveries and audit rows are queryable. SQLite same file is an educational stand-in for a downstream database, not an external service.

## Components and inputs/outputs
`src/outbox_lab/db.py`: schema, connections, transaction helpers. `service.py`: order submission/idempotency, event claims, retries, delivery, stale recovery, metrics. `api.py`: FastAPI and HTML dashboard. `cli.py`: init, submit, worker, loop, stats, demo. `tests/`: domain, failure, concurrency and API smoke. `samples/`: example JSON and captured real smoke outputs. `docs/`: architecture, research, verification, limitations. Use ISO UTC timestamps, UUIDs, JSON payloads, integer minor currency units. No personally identifying data in synthetic fixtures.

## Error cases and constraints
Reject blank or excessive idempotency keys, invalid amounts, malformed requests; conflicting idempotency keys return 409; SQLite transactions rollback if outbox insertion fails. Use SQLite busy timeout and WAL. Claims must be serialized; no duplicate effects when two workers race. Retry backoff capped; attempts bounded. Stale leases can be recovered. Do not claim exactly-once external delivery. No user-supplied SQL or arbitrary code execution.

## Implementation order
1. Save this prompt and research/selection history. 2. Implement schema and service. 3. Add CLI and API. 4. Add tests with deterministic time injection. 5. Add docs, Docker/CI and samples. 6. Run formatting/syntax checks, pytest, end-to-end API+worker smoke, inspect logs, fix and rerun. 7. Commit locally to feature branch. 8. If authenticated GitHub supports creating dedicated repository, create `Ahmad-Joker/outbox-reliability-lab`, push branch and open PR; otherwise preserve zip and report exact missing permission/capability, never push into unrelated repo. 9. Create readable explanatory PDF and save to Library; link actual downloadable file.

## Acceptance criteria
- Working order endpoint and unique idempotency semantics.
- Atomic order/outbox creation proven by rollback test.
- Worker success, transient failure/retry, dead-letter, crash-after-delivery recovery and duplicate suppression tested.
- Concurrent claims tested, meaningful HTTP and CLI smoke pass.
- README with reproducible commands, architecture and limitations; CI config; no invented performance or security claims.
- Verification record includes actual command output and any unverified steps.
- PDF explains user story, ranked ideas, source links, diagram, example actual input/output, modules, run commands, measured test outcomes, limitations, interview explanation, truthful CV bullet and GitHub status.

## Implement–test–inspect–fix loop
For each module, implement smallest complete behavior, run targeted tests, inspect failures and schema/log output, fix root cause without removing meaningful assertions, then run full tests and a fresh end-to-end smoke. Bound retries; record unresolved blockers. A successful local build is not a successful GitHub push. Mark all publishing and Docker results honestly.
