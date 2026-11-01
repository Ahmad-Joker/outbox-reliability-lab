import concurrent.futures
import sqlite3

import pytest

from outbox_lab.db import connect
from outbox_lab.service import IdempotencyConflict, InputError, OutboxService


@pytest.fixture
def service(tmp_path):
    return OutboxService(tmp_path / "test.sqlite")


def test_order_idempotency_and_conflict(service):
    first = service.create_order(1250, "abc", now=100)
    second = service.create_order(1250, "abc", now=200)
    assert first["order_id"] == second["order_id"]
    assert second == {"order_id": first["order_id"], "created": False}
    assert service.stats()["orders"] == 1
    assert len(service.list_events()) == 1
    with pytest.raises(IdempotencyConflict):
        service.create_order(1300, "abc", now=200)


@pytest.mark.parametrize("amount,key", [(0,"a"),(-1,"a"),(True,"a"),(1.2,"a"),(1,""),(1," "),(1,"x"*129)])
def test_invalid_input(service, amount, key):
    with pytest.raises(InputError):
        service.create_order(amount, key)


def test_atomic_rollback_when_outbox_insert_fails(service):
    with connect(service.path) as conn:
        conn.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT,'injected db error'); END;")
    with pytest.raises(sqlite3.IntegrityError):
        service.create_order(100, "rollback", now=100)
    assert service.stats()["orders"] == 0


def test_successful_delivery(service):
    order = service.create_order(100, "ok", now=100)
    result = service.process_one(now=100)
    assert result["outcome"] == "delivered"
    assert result["new_delivery"] is True
    assert service.get_order(order["order_id"])["status"] == "delivered"
    assert service.stats()["deliveries"] == 1
    assert service.process_one(now=100) is None


def test_retry_backoff_and_success(service):
    service.create_order(100, "retry", now=100)
    result = service.process_one(failure="before", now=100)
    assert result["outcome"] == "retry"
    assert service.process_one(now=100.5) is None
    assert service.process_one(now=101)["outcome"] == "delivered"
    assert service.stats()["deliveries"] == 1


def test_dead_letter_after_bounded_retries(service):
    service.create_order(100, "dead", now=100)
    assert service.process_one(failure="before", now=100)["outcome"] == "retry"
    assert service.process_one(failure="before", now=101)["outcome"] == "retry"
    assert service.process_one(failure="before", now=103)["outcome"] == "dead"
    assert service.process_one(now=999) is None
    assert service.stats()["deliveries"] == 0


def test_crash_after_delivery_and_idempotent_recovery(service):
    created = service.create_order(100, "crash", now=100)
    crash = service.process_one(failure="after", now=100)
    assert crash["outcome"] == "simulated_crash_after_delivery"
    assert service.stats()["deliveries"] == 1
    assert service.recover_stale(now=129) == 0
    assert service.recover_stale(now=130) == 1
    result = service.process_one(now=130)
    assert result["outcome"] == "delivered"
    assert result["new_delivery"] is False
    assert service.stats()["deliveries"] == 1
    assert service.get_order(created["order_id"])["attempts"] == 2
    assert "recovered" in [x["action"] for x in service.audit(created["event_id"])]


def test_concurrent_workers_claim_one_event(service):
    service.create_order(100, "race", now=100)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: service.process_one(now=100), range(6)))
    assert sum(result is not None for result in results) == 1
    assert service.stats()["deliveries"] == 1


def test_crashed_max_attempts_becomes_dead(service):
    s = OutboxService(service.path, max_attempts=1)
    s.create_order(100, "lease", now=100)
    assert s.process_one(failure="after", now=100)["outcome"] == "simulated_crash_after_delivery"
    assert s.recover_stale(now=130) == 1
    assert s.list_events()[0]["status"] == "dead"
    assert s.stats()["deliveries"] == 1
