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


def test_check_perform_zero_sum_uses_rpc_amount(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        return SimpleNamespace(
            id=order_id,
            payment=SimpleNamespace(value="payme"),
            payment_status=SimpleNamespace(value="to'lanmadi"),
            status=SimpleNamespace(value="yangi"),
            total_sum=0,
        )

    async def fake_amount_tiyin(_order_id):
        return 0

    async def fake_busy(_order_id):
        return False

    monkeypatch.setattr(payme_router.Order, "get_or_none", fake_get_or_none)
    monkeypatch.setattr(payme_router, "get_order_amount_tiyin", fake_amount_tiyin)
    monkeypatch.setattr(payme_router, "_payme_has_waiting_payme_receipt", fake_busy)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc(
                "CheckPerformTransaction",
                {"amount": 200000, "account": {"order_id": "1"}},
            ),
        )

    assert response.json().get("result") == {"allow": True}


def test_create_transaction_zero_sum_creates_receipt(monkeypatch):
    from fast_routers import payme as payme_router

    created: dict = {}

    async def fake_get_or_none(order_id):
        return SimpleNamespace(
            id=order_id,
            payment=SimpleNamespace(value="payme"),
            payment_status=SimpleNamespace(value="to'lanmadi"),
            status=SimpleNamespace(value="yangi"),
            total_sum=0,
        )

    async def fake_amount_tiyin(_order_id):
        return 0

    async def fake_busy(_order_id):
        return False

    async def fake_update(_order_id, **kwargs):
        created["order_update"] = kwargs

    async def fake_create(**kwargs):
        created["receipt"] = kwargs
        return SimpleNamespace(id=99, create_time=kwargs.get("create_time"))

    async def fake_execute(_query):
        class _R:
            def scalar(self):
                return None

        return _R()

    monkeypatch.setattr(payme_router.Order, "get_or_none", fake_get_or_none)
    monkeypatch.setattr(payme_router.Order, "update", fake_update)
    monkeypatch.setattr(payme_router.PaymentReceipt, "create", fake_create)
    monkeypatch.setattr(payme_router, "get_order_amount_tiyin", fake_amount_tiyin)
    monkeypatch.setattr(payme_router, "_payme_has_waiting_payme_receipt", fake_busy)
    monkeypatch.setattr(payme_router.db, "execute", fake_execute)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc(
                "CreateTransaction",
                {
                    "id": "6a26c422d3ee342047107cda",
                    "time": 1780925474031,
                    "amount": 200000,
                    "account": {"order_id": "1"},
                },
            ),
        )

    body = response.json()
    assert body["result"]["state"] == payme_router.STATE_WAITING_PAY
    assert created["receipt"]["amount"] == 200000
    assert created["order_update"]["total_sum"] == 2000
