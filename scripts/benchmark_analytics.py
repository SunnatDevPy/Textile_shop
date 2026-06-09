"""Analytics endpointlar tezligi va xatolarni tekshirish (push oldidan)."""
from __future__ import annotations

import base64
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class Result:
    label: str
    url: str
    status: int | None
    ms: float
    ok: bool
    error: str | None = None
    body_preview: str | None = None


def basic_auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def request_once(
    base_url: str,
    path: str,
    auth_header: str,
    timeout: float = 30.0,
) -> Result:
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url, headers={"Authorization": auth_header, "Accept": "application/json"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            ms = (time.perf_counter() - start) * 1000
            return Result(
                label=path,
                url=url,
                status=resp.status,
                ms=ms,
                ok=200 <= resp.status < 300,
                body_preview=body[:200],
            )
    except urllib.error.HTTPError as exc:
        ms = (time.perf_counter() - start) * 1000
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return Result(
            label=path,
            url=url,
            status=exc.code,
            ms=ms,
            ok=False,
            error=body[:300] or str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        ms = (time.perf_counter() - start) * 1000
        return Result(label=path, url=url, status=None, ms=ms, ok=False, error=str(exc))


def validate_json_fields(path: str, body: str) -> list[str]:
    issues: list[str] = []
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return [f"JSON parse: {exc}"]

    data = payload.get("data", payload)
    if path.endswith("/stats/sales"):
        for key in ("total_orders", "sales_amount", "payment_breakdown"):
            if key not in data:
                issues.append(f"missing field: {key}")
    elif path.endswith("/stats/analytics-v2"):
        for key in ("top_products", "average_check", "ltv", "sales_by_day"):
            if key not in data:
                issues.append(f"missing field: {key}")
    elif path.endswith("/stats/dashboard"):
        for key in ("today_sales", "week_sales", "top_products", "inventory_summary"):
            if key not in data:
                issues.append(f"missing field: {key}")
    return issues


def fetch_body(base_url: str, path: str, auth_header: str) -> tuple[int, str]:
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url, headers={"Authorization": auth_header, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def bench_endpoint(base_url: str, path: str, auth_header: str, runs: int = 3) -> dict:
    timings: list[float] = []
    last: Result | None = None
    validation_issues: list[str] = []

    for _ in range(runs):
        last = request_once(base_url, path, auth_header)
        timings.append(last.ms)
        if not last.ok:
            break

    if last and last.ok:
        try:
            _, body = fetch_body(base_url, path, auth_header)
            validation_issues = validate_json_fields(path, body)
        except Exception as exc:  # noqa: BLE001
            validation_issues = [str(exc)]

    return {
        "path": path,
        "status": last.status if last else None,
        "ok": last.ok if last else False,
        "error": last.error if last and not last.ok else None,
        "ms_min": min(timings) if timings else None,
        "ms_avg": statistics.mean(timings) if timings else None,
        "ms_max": max(timings) if timings else None,
        "validation_issues": validation_issues,
    }


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    label = sys.argv[2] if len(sys.argv) > 2 else "local"
    username = sys.argv[3] if len(sys.argv) > 3 else "admin"
    password = sys.argv[4] if len(sys.argv) > 4 else "1111"
    runs = int(sys.argv[5]) if len(sys.argv) > 5 else 3

    today = date.today()
    month_ago = today - timedelta(days=30)
    date_from = month_ago.isoformat()
    date_to = today.isoformat()

    auth = basic_auth_header(username, password)
    paths = [
        f"/api/history/stats/sales?date_from={date_from}&date_to={date_to}",
        f"/api/history/stats/analytics-v2?date_from={date_from}&date_to={date_to}&top_limit=10",
        "/api/history/stats/dashboard?top_limit=10",
    ]

    print(f"=== Benchmark: {label} ===")
    print(f"Base URL: {base_url}")
    print(f"Runs per endpoint: {runs}")
    print()

    failed = 0
    for path in paths:
        row = bench_endpoint(base_url, path, auth, runs=runs)
        status = "OK" if row["ok"] else "FAIL"
        if not row["ok"]:
            failed += 1
        print(f"[{status}] {row['path']}")
        print(
            f"      status={row['status']}  "
            f"min={row['ms_min']:.1f}ms  avg={row['ms_avg']:.1f}ms  max={row['ms_max']:.1f}ms"
            if row["ms_avg"] is not None
            else f"      status={row['status']}  error={row['error']}"
        )
        if row["validation_issues"]:
            print(f"      validation: {row['validation_issues']}")
            failed += 1
        if row["error"]:
            print(f"      error: {row['error']}")
        print()

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
