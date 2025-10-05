from __future__ import annotations
import time, asyncio
import httpx
from typing import Dict, Any
from .config import settings

# 단순 토큰 캐시
_token_cache: Dict[str, Any] = {"access_token": None, "exp": 0}

def _build_headers() -> Dict[str, str]:
    # 헤더에도 키 제공(호환성↑)
    return {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "appkey": settings.app_key,
        "appsecret": settings.app_secret,
        "secretkey": settings.app_secret,  # 서버에서 secretkey 라벨을 요구하는 경우 대비
    }

def _build_body() -> Dict[str, Any]:
    # 바디(JSON)에도 키 제공(이번 케이스의 핵심)
    return {
        "grant_type": "client_credentials",
        "appkey": settings.app_key,
        "appsecret": settings.app_secret,
        "secretkey": settings.app_secret,  # 호환 목적(문서/서버 구현 차이 흡수)
    }

async def _request_token_once(client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    정답 조합 1회만 시도:
      - POST https://mockapi.kiwoom.com/oauth2/token
      - 헤더: appkey/secretkey 포함
      - 바디(JSON): appkey/secretkey 포함
    """
    url = settings.base_url.rstrip("/") + "/oauth2/token"
    r = await client.post(url, headers=_build_headers(), json=_build_body(), timeout=12.0)
    txt = r.text
    try:
        body = r.json()
    except Exception:
        body = {"text": txt}

    token = None
    if isinstance(body, dict):
        token = body.get("access_token") or body.get("accessToken") or body.get("token")

    return {"status": r.status_code, "body": body, "token": token}

async def _request_token_with_retry() -> Dict[str, Any]:
    """
    429(요청 과다), 500(서버 내부오류) 같은 임시 오류에 대해 짧게 재시도.
    """
    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            res = await _request_token_once(client)
            status = res["status"]
            if status == 200 and res.get("token"):
                return {"success": True, "token": res["token"], "last": res}
            # 임시 오류면 한 번 쉬고 재시도
            if status in (429, 500):
                await asyncio.sleep(1.2)
                continue
            # 그 외 상태는 재시도 무의미 → 즉시 반환
            return {"success": False, "last": res}
    return {"success": False, "last": {"status": -1, "body": {"error": "NO_RESPONSE"}}}

# /api/token/debug 에서 쓰는 진단용(형식 단순화)
async def _request_token(client: httpx.AsyncClient) -> Dict[str, Any]:
    res = await _request_token_once(client)
    return {"success": bool(res.get("token")), "attempts": [
        {"url": settings.base_url.rstrip('/') + "/oauth2/token",
         "status": res["status"],
         "mode": "POST JSON (headers+body with keys)",
         "body": res["body"]}
    ]}

async def get_token(debug: bool = False) -> str:
    """
    성공 시 토큰 캐시(약 50분). debug=True면 실패 시 빈 문자열 반환.
    """
    now = time.time()
    if _token_cache["access_token"] and _token_cache["exp"] > now + 60:
        return _token_cache["access_token"]

    result = await _request_token_with_retry()
    if result["success"]:
        token = result["token"]
        _token_cache["access_token"] = token
        _token_cache["exp"] = now + 60 * 50
        return token

    if debug:
        return ""
    raise RuntimeError(f"Token request failed: {result.get('last')}")
