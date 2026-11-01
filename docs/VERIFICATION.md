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

## Unverified / blocked
- Docker build and Compose were **not run** because the Docker executable/daemon was unavailable.
- GitHub dedicated repository `Ahmad-Joker/outbox-reliability-lab` was not found (GitHub API 404), and the connected GitHub action set does **not** provide repository creation. `gh` CLI is not installed and no authenticated CLI alternative was available. No remote push, remote commit, GitHub Actions run, or pull request was performed. A local feature branch/commit and downloadable ZIP are provided instead. **Action needed:** create `Ahmad-Joker/outbox-reliability-lab` on GitHub, initialize with a README if convenient, and grant the connected GitHub integration access; then push a fresh feature branch and open a PR after checking the new default branch. Do not overwrite unrelated repos.
- No cloud deployment, external broker, external payment service, real-world performance benchmark, or production security review.
- `pip check` flagged an unrelated pre-existing environment conflict (moviepy vs Pillow) and was not used as a project acceptance check.

## Honest semantics
The inbox and outbox share one local SQLite file but commit separately. This exercises an idempotent downstream-effect simulation; it does not establish exactly-once delivery across real independent services. `--failure after` is a simulated process crash, not an OS process kill.
