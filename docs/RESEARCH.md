# Hiring research and selection — 2026-11-01

Official employer sources (visited in this run):
- Monzo Software Engineer Intern, London, deadline Nov 1, Go/Kafka/Docker: https://job-boards.greenhouse.io/monzo/jobs/8156261
- Amazon ML Software Development Engineer Intern, UK, reliability, CI/CD, validation: https://www.amazon.jobs/en/jobs/10588762/2027-software-dev-engineer-intern-machine-learning-uk
- Cloudflare SWE Intern 2027, London, Python/Go/distributed systems: https://job-boards.greenhouse.io/cloudflare/jobs/8245211
- Graphcore Cloud Platform Summer Intern, Bristol, deadline Nov 29, Linux/scripting/CI/monitoring: https://job-boards.greenhouse.io/graphcore/jobs/8894965002
- Aleph Finance Automation Intern, Cairo, hybrid, reconciliation and reporting: https://jobs.lever.co/aleph/f6da715d-f67e-4c25-bab1-b2e5d14709d0
- Perplexity Search ML Intern, London, retrieval/ranking/RAG/evaluation: https://jobs.ashbyhq.com/perplexity/71168628-1998-47d3-87a9-be7bc56a430d

Recurring needs: clean Python/Go, SQL and data consistency, robust APIs, asynchronous workflows, reproducible tests, CI/CD, logging, operational debugging, ML/RAG evaluation. Ahmad's accessible Oct 29 CV shows DataPilot evaluation and SolutionForge tests, HireReady CV and Python ML work. Distinct gap: explicit failure-tolerant backend transaction design with independently reproducible tests. Remote-from-Egypt eligibility was not verified for the UK onsite roles.

Editorial weighted scoring (0–5 per dimension): hiring demand 25%; gap 20%; usefulness 15%; differentiation 15%; feasibility 15%; cost 10%.

| Idea | Hiring | Gap | Useful | Different | Feasible | Low cost | Weighted /100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Outbox Reliability Lab | 5 | 5 | 5 | 4 | 5 | 5 | 97 |
| ReconcileAudit | 4 | 4 | 5 | 3 | 5 | 5 | 85 |
| SearchRankBench | 5 | 4 | 4 | 4 | 3 | 4 | 82 |
| EdgeVisionOps | 4 | 4 | 4 | 5 | 2 | 3 | 75 |

Competitors: Temporal (https://docs.temporal.io/design-patterns) is a production durable-workflow platform; Celery and Kafka offer mature queues/brokers; microservices.io documents transactional outbox and idempotent consumer patterns. This lab does not replace those products. It provides a minimal, zero-credential, fault-injection educational demonstration.

Sources: https://microservices.io/patterns/communication-style/idempotent-consumer.html ; https://microservices.io/patterns/data/polling-publisher.html .
