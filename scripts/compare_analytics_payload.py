"""Production vs local analytics javoblarini solishtirish."""
from __future__ import annotations

import base64
import json
import sys
import urllib.request


def fetch(url: str, user: str, password: str) -> dict:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def pick_sales(d: dict) -> dict:
    return {
        "total_orders": d.get("total_orders"),
        "paid_orders": d.get("paid_orders"),
        "sales_amount": d.get("sales_amount"),
        "sold_items_count": d.get("sold_items_count"),
    }


def pick_analytics(d: dict) -> dict:
    return {
        "sold_orders_count": d.get("average_check", {}).get("sold_orders_count"),
        "sold_orders_revenue": d.get("average_check", {}).get("sold_orders_revenue"),
        "avg_check": d.get("average_check", {}).get("avg_check"),
        "customers_count": d.get("ltv", {}).get("customers_count"),
        "top_products_len": len(d.get("top_products") or []),
        "sales_by_day_len": len(d.get("sales_by_day") or []),
    }


def pick_dashboard(d: dict) -> dict:
    return {
        "today_revenue": d.get("today_sales", {}).get("revenue"),
        "week_revenue": d.get("week_sales", {}).get("revenue"),
        "new_orders": d.get("new_orders"),
        "top_products_len": len(d.get("top_products") or []),
        "inventory_products": d.get("inventory_summary", {}).get("products_count"),
    }


def main() -> int:
    prod = sys.argv[1]
    local = sys.argv[2]
    user = sys.argv[3] if len(sys.argv) > 3 else "admin"
    password = sys.argv[4] if len(sys.argv) > 4 else "1111"
    q = "?date_from=2026-05-10&date_to=2026-06-09"

    checks = [
        ("sales", f"/api/history/stats/sales{q}", pick_sales),
        ("analytics-v2", f"/api/history/stats/analytics-v2{q}&top_limit=10", pick_analytics),
        ("dashboard", "/api/history/stats/dashboard?top_limit=10", pick_dashboard),
    ]

    print("=== Payload comparison (prod vs local) ===")
    mismatches = 0
    for name, path, picker in checks:
        prod_data = fetch(f"{prod.rstrip('/')}{path}", user, password).get("data", {})
        local_data = fetch(f"{local.rstrip('/')}{path}", user, password).get("data", {})
        prod_pick = picker(prod_data)
        local_pick = picker(local_data)
        same = prod_pick == local_pick
        status = "MATCH" if same else "DIFF"
        if not same:
            mismatches += 1
        print(f"[{status}] {name}")
        print(f"  prod : {prod_pick}")
        print(f"  local: {local_pick}")
        print()
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
