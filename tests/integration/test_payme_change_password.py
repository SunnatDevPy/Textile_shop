import base64

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


def _payme_headers(secret: str | None = None) -> dict[str, str]:
    pwd = (secret or conf.PAYME_SECRET_KEY or "test-secret").strip()
    token = base64.b64encode(f"Paycom:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_change_password_sandbox_flow(monkeypatch):
    from fast_routers import payme as payme_router

    old_secret = "oldSecretForPaymeTest12"
    new_secret = "newSecretForPaymeTest99"
    monkeypatch.setattr(conf, "PAYME_SECRET_KEY", old_secret)
    monkeypatch.setattr(payme_router, "_payme_secret_runtime_override", None)
    monkeypatch.setattr(payme_router, "_read_payme_secret_runtime_file", lambda: None)
    monkeypatch.setattr(payme_router, "_persist_payme_secret_runtime_file", lambda _s: None)

    with TestClient(app) as client:
        change = client.post(
            "/api/payme",
            headers=_payme_headers(old_secret),
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "ChangePassword",
                "params": {"password": new_secret},
            },
        )
        old_auth = client.post(
            "/api/payme",
            headers=_payme_headers(old_secret),
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "CheckTransaction",
                "params": {"id": "missing"},
            },
        )
        new_auth = client.post(
            "/api/payme",
            headers=_payme_headers(new_secret),
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "ChangePassword",
                "params": {"password": "anotherSecretKey456"},
            },
        )

    assert change.json().get("result") == {"success": True}
    assert old_auth.json()["error"]["code"] == payme_router.PaymeError.INSUFFICIENT_PRIVILEGE
    assert new_auth.json().get("result") == {"success": True}
