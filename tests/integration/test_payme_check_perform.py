import base64
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from config import conf
from main import app
from models import Order


PAYME_ACCOUNT_ERROR_MIN = -31099
PAYME_ACCOUNT_ERROR_MAX = -31050


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
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}


def _awaiting_order(order_id: int = 7):
    return SimpleNamespace(
        id=order_id,
        payment=Order.Payment.PAYME,
        payment_status=Order.PaymentStatus.UNPAID,
        status=Order.StatusOrder.NEW,
    )


def _blocked_order(order_id: int = 8):
    return SimpleNamespace(
        id=order_id,
        payment=Order.Payment.PAYME,
        payment_status=Order.PaymentStatus.PAID,
        status=Order.StatusOrder.NEW,
    )


def test_check_perform_awaiting_payment_allow_true(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        return _awaiting_order(order_id)

    async def fake_amount_tiyin(_order_id):
        return 1_100_000

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
                {"amount": 1_100_000, "account": {"order_id": "7"}},
            ),
        )

    body = response.json()
    assert body.get("result") == {"allow": True}


def test_check_perform_pending_payment_allow_true(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        order = _awaiting_order(order_id)
        order.payment = Order.Payment.PENDING
        return order

    async def fake_amount_tiyin(_order_id):
        return 500_000

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
                {"amount": 500_000, "account": {"order_id": "7"}},
            ),
        )

    assert response.json().get("result") == {"allow": True}


def test_check_perform_processing_account_error_in_range(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        return _awaiting_order(order_id)

    async def fake_amount_tiyin(_order_id):
        return 1_100_000

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
                {"amount": 1_100_000, "account": {"order_id": "7"}},
            ),
        )

    code = response.json()["error"]["code"]
    assert PAYME_ACCOUNT_ERROR_MIN <= code <= PAYME_ACCOUNT_ERROR_MAX
    assert response.json()["error"]["data"] == "order_id"


def test_check_perform_blocked_account_error_in_range(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(order_id):
        return _blocked_order(order_id)

    monkeypatch.setattr(payme_router.Order, "get_or_none", fake_get_or_none)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc(
                "CheckPerformTransaction",
                {"amount": 1_100_000, "account": {"order_id": "8"}},
            ),
        )

    code = response.json()["error"]["code"]
    assert PAYME_ACCOUNT_ERROR_MIN <= code <= PAYME_ACCOUNT_ERROR_MAX
    assert response.json()["error"]["data"] == "order_id"


def test_check_perform_not_found_account_error_in_range(monkeypatch):
    from fast_routers import payme as payme_router

    async def fake_get_or_none(_order_id):
        return None

    monkeypatch.setattr(payme_router.Order, "get_or_none", fake_get_or_none)

    with TestClient(app) as client:
        response = client.post(
            "/api/payme",
            headers=_payme_headers(),
            json=_rpc(
                "CheckPerformTransaction",
                {"amount": 1_100_000, "account": {"order_id": "99999"}},
            ),
        )

    code = response.json()["error"]["code"]
    assert PAYME_ACCOUNT_ERROR_MIN <= code <= PAYME_ACCOUNT_ERROR_MAX
    assert response.json()["error"]["data"] == "order_id"
