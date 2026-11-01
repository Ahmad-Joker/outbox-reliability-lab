# Architecture and design decisions

```
                HTTP (idempotency key)
                        |
                    FastAPI
                        |
             BEGIN IMMEDIATE + COMMIT
                        |
                SQLite database
                /             \
          orders            outbox (queued)
                                |
                         polling worker
                       claim + lease/attempt
                                |
                     simulated inbox INSERT
                        UNIQUE(event_id)
                                |
                  ack / retry / dead letter
                                |
                     audit + dashboard
```

**Atomicity:** order and outbox insertion are in one database transaction. An injected SQL trigger failure rolls back both.

**Delivery:** worker claim is serialized with `BEGIN IMMEDIATE`. The inbox is separately committed. A simulated crash after inbox commit leaves outbox `processing`; recovery after 30-second lease changes it to `retry`. Redelivery sees existing `event_id` and performs no second simulated effect.

**At-least-once:** retries may repeat attempts. Idempotency is provided by the simulated receiver, not a promise of exactly-once delivery to arbitrary external services. A real remote receiver must persist its own idempotency keys.

**Retry:** 1, 2, 4... seconds, capped at 60 seconds. Max attempts 3; after that dead-letter state. An expired lease at max attempts also becomes dead. For a real system, retries should classify transient vs permanent errors and support manual re-drive.

**Security:** No remote side effects, no SQL interpolation, no secrets or PII fixtures. The API has no authentication and must not be publicly exposed as-is. Docker/CI are templates until independently verified.

**Data flow:** `OrderRequest` (amount_cents integer) + `Idempotency-Key` -> `orders` + `outbox` -> `deliveries` -> `audit` and `/stats`. Money is integer cents; no floats for money. Timestamps stored as UTC epoch seconds, converted to ISO UTC in order/audit responses.
