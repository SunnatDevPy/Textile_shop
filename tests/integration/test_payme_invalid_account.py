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


def test_check_perform_zero_sum_returns_invalid_account(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        return SimpleNamespace(
            id=order_id,
            payment=SimpleNamespace(value="payme"),
            payment_status=SimpleNamespace(value="to'lanmadi"),
            status=SimpleNamespace(value="yangi"),
        )

    async def fake_amount_tiyin(_order_id):
        return 0

    async def fake_busy(_order_id):
        return True

    monkeypatch.setattr(payme_router.Order, "get_or_none", fake_get_or_none)
    monkeypatch.setattr(payme_router, "get_order_amount_tiyin", fake_amount_tiyin)
    monkeypatch.setattr(payme_router, "_payme_has_waiting_payme_receipt", fake_busy)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc(
                "CheckPerformTransaction",
                {"amount": 22222, "account": {"order_id": "5"}},
            ),
        )

    body = response.json()
    assert body["error"]["code"] == payme_router.PaymeError.INVALID_ACCOUNT
    assert body["error"]["data"] == "order_id"


def test_create_transaction_zero_sum_returns_invalid_account(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        return SimpleNamespace(
            id=order_id,
            payment=SimpleNamespace(value="payme"),
            payment_status=SimpleNamespace(value="to'lanmadi"),
            status=SimpleNamespace(value="yangi"),
        )

    async def fake_amount_tiyin(_order_id):
        return 0

    async def fake_execute(_query):
        class _R:
            def scalar(self):
                return None

        return _R()

    monkeypatch.setattr(payme_router.Order, "get_or_none", fake_get_or_none)
    monkeypatch.setattr(payme_router, "get_order_amount_tiyin", fake_amount_tiyin)
    monkeypatch.setattr(payme_router.db, "execute", fake_execute)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc(
                "CreateTransaction",
                {
                    "id": "6a26bca9d3ee342047107cba",
                    "time": 1780923561677,
                    "amount": 22222,
                    "account": {"order_id": "5"},
                },
            ),
        )

    body = response.json()
    assert body["error"]["code"] == payme_router.PaymeError.INVALID_ACCOUNT
    assert body["error"]["data"] == "order_id"
