# backend/app/kiwoom.py
from __future__ import annotations

import httpx
from .auth import get_token
from .config import settings

BASE = settings.base_url.rstrip("/")  # e.g. https://mockapi.kiwoom.com
JSON_HEADERS = {"content-type": "application/json; charset=UTF-8"}


def _std_headers(api_id: str, token: str) -> dict:
    return {
        **JSON_HEADERS,
        "authorization": f"Bearer {token}",
        "appkey": settings.app_key,
        "appsecret": settings.app_secret,
        "api-id": api_id,
    }


async def _post_json(path: str, api_id: str, payload: dict, extra_headers: dict | None = None):
    """
    공통 POST(JSON). (status, body, headers) 반환
    """
    token = await get_token()
    url = f"{BASE}{path}"
    headers = _std_headers(api_id, token)
    if extra_headers:
        headers.update(extra_headers)

    async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
        r = await client.post(url, headers=headers, json=payload)

    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text}
    return r.status_code, body, dict(r.headers)


async def _try_many(candidates: list[tuple[str, str]], payload: dict) -> dict:
    """
    여러 후보 (path, api_id) 를 순차 시도.
    성공 시: {"ok": True, "status": 200, "body": ..., "headers": ..., "endpoint": (path, api_id)}
    실패 시: {"ok": False, "status": 마지막상태, "body": 마지막본문, "trace": [각 시도 결과...]}
    """
    trace: list[dict] = []
    last_status = None
    last_body = None
    last_headers = None
    last_endpoint = None

    for path, api_id in candidates:
        status, body, headers = await _post_json(path, api_id, payload)
        trace.append({"path": path, "api_id": api_id, "status": status, "body": body})
        last_status, last_body, last_headers, last_endpoint = status, body, headers, (path, api_id)
        if status == 200:
            return {
                "ok": True,
                "status": status,
                "body": body,
                "headers": headers,
                "endpoint": (path, api_id),
                "trace": trace,
            }

    return {
        "ok": False,
        "status": last_status,
        "body": last_body,
        "headers": last_headers,
        "endpoint": last_endpoint,
        "trace": trace,
    }


# ───────────────────────────────────────────────────────────────────────────────
# 주문 (모의: /api/dostk/ordr)
#   - kt10000 : 현금매수
#   - kt10001 : 현금매도
#   * ord_qty, ord_prc 는 문자열
# ───────────────────────────────────────────────────────────────────────────────
ORDER_PATH = "/api/dostk/ordr"


async def order_cash(
    code: str,
    qty: int,
    is_buy: bool,
    is_market: bool,
    price: int,
    idempotency_key: str | None = None,
):
    api_id = "kt10000" if is_buy else "kt10001"
    ord_dvsn = "01" if is_market else "00"  # 01=시장가, 00=지정가(모의는 지정가 제한)

    payload = {
        "CANO": settings.account_no,
        "ACNT_PRDT_CD": settings.acnt_prdt_cd,
        "pdno": code,
        "ord_dvsn": ord_dvsn,
        "ord_qty": str(int(qty)),                           # 문자열!
        "ord_prc": str(0 if is_market else int(price)),    # 문자열!
    }
    headers = {}
    if idempotency_key:
        headers["x-idempotency-key"] = idempotency_key

    return await _post_json(ORDER_PATH, api_id, payload, headers)


# ───────────────────────────────────────────────────────────────────────────────
# 계좌 조회 (모의 환경 후보 URI 다중 시도)
#   - 예수금(kt00001) 후보:
#       /api/dsacc/deposit, /api/accno/deposit, /api/acc/deposit
#   - 잔고합계(kt00017) 후보:
#       /api/dsacc/balance, /api/accno/balance, /api/acc/balance
# ───────────────────────────────────────────────────────────────────────────────
DEPOSIT_CANDIDATES = [
    ("/api/dsacc/deposit", "kt00001"),
    ("/api/accno/deposit", "kt00001"),
    ("/api/acc/deposit", "kt00001"),
]

BALANCE_CANDIDATES = [
    ("/api/dsacc/balance", "kt00017"),
    ("/api/accno/balance", "kt00017"),
    ("/api/acc/balance", "kt00017"),
]


def _acct_payload() -> dict:
    return {
        "CANO": settings.account_no,
        "ACNT_PRDT_CD": settings.acnt_prdt_cd,
    }


def _pick_first(d: dict, keys: list[str], default=0):
    for k in keys:
        if k in d:
            return d[k]
    return default


def _to_int(v) -> int:
    try:
        if isinstance(v, str):
            v = v.replace(",", "").strip()
        return int(float(v))
    except Exception:
        return 0


def _to_float(v) -> float:
    try:
        if isinstance(v, str):
            v = v.replace("%", "").replace(",", "").strip()
        return float(v)
    except Exception:
        return 0.0


async def fetch_deposit() -> dict:
    trial = await _try_many(DEPOSIT_CANDIDATES, _acct_payload())
    if not trial["ok"]:
        return {"ok": False, "trace": trial["trace"], "status": trial["status"], "body": trial["body"]}

    body = trial["body"]
    deposit = _pick_first(body, ["예수금", "deposit", "DEPOSIT"], default=0)
    orderable = _pick_first(body, ["주문가능금액", "orderable_cash", "ORD_PSB"], default=0)
    return {
        "ok": True,
        "deposit": _to_int(deposit),
        "orderable": _to_int(orderable),
        "raw": body,
        "endpoint": trial.get("endpoint"),
        "trace": trial.get("trace", []),
    }


async def fetch_balance() -> dict:
    trial = await _try_many(BALANCE_CANDIDATES, _acct_payload())
    if not trial["ok"]:
        return {"ok": False, "trace": trial["trace"], "status": trial["status"], "body": trial["body"]}

    body = trial["body"]
    total_purchase = _pick_first(body, ["총매입금액", "total_purchase"], default=0)
    total_eval = _pick_first(body, ["총평가금액", "total_eval"], default=0)
    total_pl = _pick_first(body, ["총평가손익금액", "total_pl"], default=0)
    total_return = _pick_first(body, ["총수익률(%)", "total_return"], default=0.0)
    today_realized = _pick_first(body, ["당일실현손익", "today_realized_pl"], default=0)

    return {
        "ok": True,
        "total_purchase": _to_int(total_purchase),
        "total_eval": _to_int(total_eval),
        "total_pl": _to_int(total_pl),
        "total_return": _to_float(total_return),
        "today_realized": _to_int(today_realized),
        "raw": body,
        "endpoint": trial.get("endpoint"),
        "trace": trial.get("trace", []),
    }
