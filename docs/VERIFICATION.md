# Verification and publication record — 2026-11-01

## Completed locally
- Python 3.13.5; FastAPI 0.128.2; pytest 9.0.2; httpx 0.28.1.
- `PYTHONPATH=src python -m pytest -q`: **16 passed**.
- `python -m compileall -q src tests`: **passed**.
- `python -m pip install -e '.[dev]' --no-build-isolation --no-deps`: **passed** using already installed packages.
- `python -m pytest -q` after local editable install: **16 passed**.
- `outbox-lab --db /tmp/outbox-demo-20261101.sqlite demo`: **passed**; injected failure -> retry -> delivered, crash after downstream commit -> stale lease recovery -> duplicate suppressed. Synthetic sample stats: 2 orders, 2 deliveries, 2 delivered events, 10 audit entries. See `samples/verified_demo_output.json`.
- FastAPI TestClient end-to-end POST order -> worker -> GET delivered order -> dashboard/stats: **passed**. Returned HTTP 201 create, HTTP 200 read, one simulated downstream delivery.
- Additional test coverage: duplicate idempotency key/conflicting amount, rollback when outbox insert fails, invalid inputs, bounded retry and dead-letter, concurrent worker claim, crash-after-delivery recovery.

## Investigated and resolved local install blocker
Initial `python -m pip install -e '.[dev]'` failed during build isolation: no network DNS resolution for PyPI (`Temporary failure in name resolution`, could not fetch `setuptools>=68`). Local `setuptools 82.0.1` was already installed. Resolved with `--no-build-isolation --no-deps` for this environment and reran tests and smoke. Standard pip install remains documented for a normal network-enabled development machine. This fix did not remove any test or acceptance criterion.

## Remaining unverified items
- Docker build and Compose were **not run** because the Docker executable/daemon was unavailable.
- No cloud deployment, external broker, external payment service, real-world performance benchmark, or production security review.
- `pip check` flagged an unrelated pre-existing environment conflict (moviepy vs Pillow) and was not used as a project acceptance check.

## Honest semantics
The inbox and outbox share one local SQLite file but commit separately. This exercises an idempotent downstream-effect simulation; it does not establish exactly-once delivery across real independent services. `--failure after` is a simulated process crash, not an OS process kill.

## Publication completed — 2026-11-01
- Recovered the saved source archive and explanatory PDF from `/CV Projects/Outbox Reliability Lab/`.
- Confirmed the PDF in the archive matches the separately saved PDF byte for byte.
- Confirmed `Ahmad-Joker/outbox-reliability-lab` exists; based the feature branch on its existing `main` commit `4dcdf91761b8b8c643785f72cf09d6f9759eab74`.
- Published the source, PDF, tests and CI configuration to `feat/outbox-reliability-mvp`.
- Opened [PR #1](https://github.com/Ahmad-Joker/outbox-reliability-lab/pull/1) against `main`. The PR remains unmerged.
- Reverified on Python 3.12.14: `python3 -m compileall -q src tests` passed; `python3 -m pytest -q` passed all **16 tests**. The HTTP smoke test passed with one Starlette/httpx deprecation warning.
- `python3 -m outbox_lab.cli --db /tmp/outbox-publish-demo-20261101.sqlite demo` passed: two orders, two deliveries, two delivered events, ten audit records, successful retry and duplicate suppression after simulated crash recovery.
- Initial upload failed with GitHub 403 because the connector was authorized but not installed on the account. Publication succeeded after installation and access were confirmed.
- GitHub Actions Python CI passed for source commit `2f616a118aa1f591ea7595e17318a10c9f748022`: [run 41293433864](https://github.com/Ahmad-Joker/outbox-reliability-lab/actions/runs/41293433864). Subsequent documentation commits have their own check status on the PR.
- The explanatory PDF records the original build and verification; this file is the current publication record.
