import base64
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from config import conf
from main import app


@pytest.fixture(autouse=True)
def _mock_startup_db(monkeypatch):
    from main import db as app_db

    async def _noop_create_all():
        return None

    monkeypatch.setattr(app_db, "create_all", _noop_create_all)


def _payme_headers() -> dict[str, str]:
    secret = (conf.PAYME_SECRET_KEY or "test-secret").strip()
    token = base64.b64encode(f"Paycom:{secret}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _rpc(method: str, params: dict, req_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }


def test_get_statement_empty_period(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_execute(_query):
        class _Result:
            def scalars(self):
                return self

            def all(self):
                return []

        return _Result()

    monkeypatch.setattr(payme_router.db, "execute", fake_execute)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc("GetStatement", {"from": 1, "to": 5}),
        )

    body = response.json()
    assert body.get("result") == {"transactions": []}


def test_get_statement_invalid_period(monkeypatch):
    from fast_routers import payme as payme_router

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc("GetStatement", {"from": 10, "to": 5}),
        )
        missing_to = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc("GetStatement", {"from": 1}, req_id=2),
        )

    body = response.json()
    assert body["error"]["code"] == payme_router.PaymeError.INVALID_ACCOUNT
    assert body["error"]["data"] == "from"

    body_to = missing_to.json()
    assert body_to["error"]["code"] == -31050
    assert body_to["error"]["data"] == "to"


def test_get_statement_returns_sorted_transactions(monkeypatch):
    from fast_routers import payme as payme_router

    receipts = [
        SimpleNamespace(
            transaction_id="tx_b",
            create_time=3,
            amount=200000,
            order_id=1,
            id=2,
            perform_time=4,
            cancel_time=None,
            reason=None,
            state=2,
            payment_system="payme",
            receipt_data='{"account":{"order_id":"1"}}',
        ),
        SimpleNamespace(
            transaction_id="tx_a",
            create_time=2,
            amount=100000,
            order_id=2,
            id=1,
            perform_time=None,
            cancel_time=None,
            reason=None,
            state=0,
            payment_system="payme",
            receipt_data='{"account":{"order_id":"2"}}',
        ),
    ]

    async def fake_execute(_query):
        class _Result:
            def scalars(self):
                return self

            def all(self):
                return receipts

        return _Result()

    monkeypatch.setattr(payme_router.db, "execute", fake_execute)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc("GetStatement", {"from": 1, "to": 5}),
        )

    body = response.json()
    txs = body["result"]["transactions"]
    assert len(txs) == 2
    assert txs[0]["id"] == "tx_b"
    assert txs[0]["time"] == 3
    assert txs[0]["account"] == {"order_id": "1"}
    assert txs[0]["state"] == 2
    assert txs[0]["perform_time"] == 4
    assert txs[0]["cancel_time"] == 0
    assert txs[0]["reason"] is None
    assert txs[1]["state"] == 1
    assert txs[1]["perform_time"] == 0
