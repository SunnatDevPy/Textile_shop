from types import SimpleNamespace

from fastapi.testclient import TestClient

from fast_routers.admin_auth import verify_admin_credentials
from main import app


class DummyScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class DummyExecuteResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return DummyScalarResult(self._rows)


def _auth_override():
    return SimpleNamespace(id=1, username="operator", status="operator", is_active=True)


def test_product_search_endpoint(monkeypatch):
    from fast_routers import products as products_router

    async def fake_search(search, category_id):
        return [{"id": 1, "name_uz": "ip"}]

    monkeypatch.setattr(products_router.Product, "search", fake_search)
    app.dependency_overrides[verify_admin_credentials] = _auth_override
    client = TestClient(app)

    response = client.get("/products/search", params={"search": "ip"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)

    app.dependency_overrides.clear()


def test_order_search_endpoint(monkeypatch):
    from fast_routers import orders as orders_router

    async def fake_execute(_query):
        return DummyExecuteResult([{"id": 10, "status": "yangi"}])

    monkeypatch.setattr(orders_router.db, "execute", fake_execute)
    app.dependency_overrides[verify_admin_credentials] = _auth_override
    client = TestClient(app)

    response = client.get("/order/search", params={"status_q": "yangi"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["meta"]["count"] == 1

    app.dependency_overrides.clear()


def test_click_prepare_endpoint(monkeypatch):
    from fast_routers import payments as payments_router

    async def fake_get_or_none(order_id):
        return SimpleNamespace(id=order_id, payment="click", status="yangi")

    monkeypatch.setattr(payments_router.Order, "get_or_none", fake_get_or_none)
    client = TestClient(app)

    response = client.post("/payments/click/prepare", json={"order_id": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["order_id"] == 1
