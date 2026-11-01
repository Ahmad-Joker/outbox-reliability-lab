from fastapi.testclient import TestClient
from outbox_lab.api import create_app
from outbox_lab.service import OutboxService


def test_http_primary_flow(tmp_path):
    db = tmp_path / "api.sqlite"
    client = TestClient(create_app(db))
    assert client.get("/health").json()["status"] == "ok"
    assert client.post("/orders", json={"amount_cents": 200}).status_code == 400
    assert client.post("/orders", headers={"Idempotency-Key": "x"}, json={"amount_cents": -1}).status_code == 422
    first = client.post("/orders", headers={"Idempotency-Key": "x"}, json={"amount_cents": 200})
    assert first.status_code == 201
    assert first.json()["created"] is True
    repeat = client.post("/orders", headers={"Idempotency-Key": "x"}, json={"amount_cents": 200})
    assert repeat.json()["created"] is False
    assert client.post("/orders", headers={"Idempotency-Key": "x"}, json={"amount_cents": 300}).status_code == 409
    assert client.get("/orders/unknown").status_code == 404
    assert OutboxService(db).process_one()["outcome"] == "delivered"
    assert client.get(f"/orders/{first.json()['order_id']}").json()["status"] == "delivered"
    assert client.get("/stats").json()["deliveries"] == 1
    assert "Outbox Reliability Lab" in client.get("/dashboard").text
    assert len(client.get("/events").json()) == 1
    assert len(client.get(f"/events/{first.json()['event_id']}/audit").json()) >= 2
