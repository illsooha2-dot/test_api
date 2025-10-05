# backend/app/routes_account.py
from typing import Any, Dict
import httpx
from fastapi import APIRouter

from .config import settings
from .auth import get_token

router = APIRouter(prefix="/api/account", tags=["account"])

BASE = settings.base_url.rstrip("/")  # ex) https://mockapi.kiwoom.com

def _to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return int(x)
        return int(str(x).replace(",", "").strip())
    except Exception:
        return default

def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(str(x).replace("%", "").strip())
    except Exception:
        return default

async def _auth_headers(token: str, tr_id: str) -> Dict[str, str]:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": settings.APP_KEY,
        "appsecret": settings.APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }

@router.get("/summary")
async def get_account_summary():
    """
    통합 계좌 요약:
      - deposit(총 예수금)
      - orderable(주문가능)
      - today_realized(오늘 실현손익)
      - total_purchase(총 매입금액)
      - total_eval(총 평가금액)
      - total_pl(총 평가손익)
      - total_return(총 수익률)
    """
    token = await get_token()
    cano = settings.ACCOUNT_NO
    prdt = settings.ACNT_PRDT_CD

    deposit = 0
    orderable = 0
    today_realized = 0
    total_purchase = 0
    total_eval = 0
    total_pl = 0
    total_return = 0.0
    errors = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1) 잔고/평가
        try:
            url_bal = f"{BASE}/uapi/domestic-stock/v1/trading/inquire-balance"
            hdr = await _auth_headers(token, tr_id="VTTC8434R")  # 모의 조회용 예시
            params_bal = {
                "CANO": cano,
                "ACNT_PRDT_CD": prdt,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "N",
                "INQR_DVSN_1": "",
                "INQR_DVSN_2": "",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            }
            rb = await client.get(url_bal, headers=hdr, params=params_bal)
            jb = rb.json() if rb.headers.get("content-type", "").startswith("application/json") else {}
            out1 = (jb.get("output1") or [{}])[0]

            total_purchase = _to_int(out1.get("pchs_amt_smtby", total_purchase))
            total_eval     = _to_int(out1.get("tot_evlu_amt", total_eval))
            total_pl       = _to_int(out1.get("evlu_pfls_smtby", total_pl))
            total_return   = _to_float(out1.get("evlu_erng_rt", total_return))

            deposit_tmp   = _to_int(out1.get("dnca_tot_amt", 0))
            order_tmp     = _to_int(out1.get("ord_psbl_cash", 0))
            if deposit_tmp:
                deposit = deposit_tmp
            if order_tmp:
                orderable = order_tmp

            for k in ("prdy_cprs_pl", "thdt_pnl_amt", "tdts_unstt_amt"):
                v = _to_int(out1.get(k, 0))
                if v:
                    today_realized = v
                    break

        except Exception as e:
            errors.append(f"balance:{type(e).__name__}:{e}")

        # 2) 예수금/주문가능
        try:
            url_dep = f"{BASE}/uapi/domestic-stock/v1/trading/inquire-psbl-deposit"
            hdr = await _auth_headers(token, tr_id="VTTC8976R")  # 모의 조회용 예시
            params_dep = {"CANO": cano, "ACNT_PRDT_CD": prdt}
            rd = await client.get(url_dep, headers=hdr, params=params_dep)
            jd = rd.json() if rd.headers.get("content-type", "").startswith("application/json") else {}
            out = (jd.get("output") or [{}])[0]

            for k in ("dnca_tot_amt", "dnca_tot_amt_won", "dnca_tot", "deposit"):
                deposit = _to_int(out.get(k, deposit))

            for k in ("ord_psbl_cash", "ord_psbl_amt", "orderable_cash", "orderable"):
                orderable = _to_int(out.get(k, orderable))

        except Exception as e:
            errors.append(f"deposit:{type(e).__name__}:{e}")

    return {
        "ok": True,
        "errors": errors,
        "deposit": deposit,
        "orderable": orderable,
        "today_realized": today_realized,
        "total_purchase": total_purchase,
        "total_eval": total_eval,
        "total_pl": total_pl,
        "total_return": total_return,
    }

@router.get("/summary/debug")
async def get_account_summary_debug():
    """디버그용(문제 생기면 여길 먼저 봄)"""
    return {
        "base": settings.base_url,
        "account": settings.ACCOUNT_NO,
        "product": settings.ACNT_PRDT_CD,
        "note": "이 값들이 맞는데도 4xx/5xx면 토큰/트래픽 혹은 모의서버 상태 문제일 확률 높음.",
    }
