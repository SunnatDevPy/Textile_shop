"""Payme integratsiyasini lokal tekshirish."""
import asyncio
import base64
import json
import time
import uuid

from config import conf
from fastapi.testclient import TestClient
from main import app
from models import Order
from models.database import db
from sqlalchemy import select
from utils.payment_links import build_payme_checkout_url, get_order_amount_tiyin


async def find_payme_order() -> int | None:
    res = await db.execute(
        select(Order)
        .where(Order.payment == "payme", Order.status == "yangi")
        .order_by(Order.id.desc())
        .limit(1)
    )
    order = res.scalar()
    return int(order.id) if order else None


def main() -> None:
    client = TestClient(app)
    secret = conf.PAYME_SECRET_KEY or ""
    auth = "Basic " + base64.b64encode(f"Paycom:{secret}".encode()).decode()
    headers = {"Authorization": auth, "Content-Type": "application/json"}

    print("=== 1. CONFIG ===")
    print("MERCHANT_ID:", conf.PAYME_MERCHANT_ID)
    print("SECRET loaded:", bool(secret.strip()))
    payme_item = next(x for x in client.get("/api/payments/list").json()["data"] if x["method"] == "payme")
    print("payments/list payme.status:", payme_item["status"])

    oid = asyncio.run(find_payme_order())
    if oid is None:
        print("\nNo payme/yangi order. Create one: POST /api/order payment=payme")
        return
    tiyin = asyncio.run(get_order_amount_tiyin(oid))
    url = build_payme_checkout_url(oid, tiyin)

    print("\n=== 2. ORDER ===")
    print("order_id:", oid)
    print("amount_tiyin:", tiyin)
    print("checkout_url:", url[:100] + "...")

    r_url = client.get(f"/api/payment-url/{oid}/payme")
    print("\n=== 3. GET payment-url ===")
    print("status:", r_url.status_code)

    cp = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "CheckPerformTransaction",
        "params": {"amount": tiyin, "account": {"order_id": str(oid)}},
    }
    r_cp = client.post("/api/payme", headers=headers, json=cp)
    body_cp = r_cp.json()
    print("\n=== 4. CheckPerformTransaction ===")
    print(json.dumps(body_cp, ensure_ascii=False))
    ok_cp = "result" in body_cp and body_cp["result"].get("allow") is True

    tx = str(uuid.uuid4())
    cr = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "CreateTransaction",
        "params": {
            "id": tx,
            "time": int(time.time() * 1000),
            "amount": tiyin,
            "account": {"order_id": str(oid)},
        },
    }
    r_cr = client.post("/api/payme", headers=headers, json=cr)
    body_cr = r_cr.json()
    print("\n=== 5. CreateTransaction ===")
    print(json.dumps(body_cr, ensure_ascii=False))
    ok_cr = "result" in body_cr

    pf = {"jsonrpc": "2.0", "id": 3, "method": "PerformTransaction", "params": {"id": tx}}
    r_pf = client.post("/api/payme", headers=headers, json=pf)
    body_pf = r_pf.json()
    print("\n=== 6. PerformTransaction ===")
    print(json.dumps(body_pf, ensure_ascii=False))
    ok_pf = "result" in body_pf and body_pf["result"].get("state") == 2

    order = asyncio.run(Order.get_or_none(oid))
    paid = order and str(order.status) == "to'landi"

    print("\n=== 7. SUMMARY ===")
    print("payment list:", "OK" if payme_item["status"] else "FAIL")
    print("CheckPerform:", "OK" if ok_cp else "FAIL")
    print("Create:", "OK" if ok_cr else "FAIL")
    print("Perform:", "OK" if ok_pf else "FAIL")
    print("Order paid:", "OK" if paid else "FAIL")


if __name__ == "__main__":
    main()
