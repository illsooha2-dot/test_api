# backend/app/routes_misc.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .storage import (
    load_settings, save_settings,
    load_telegram_settings, save_telegram_settings,
)
from .auth import get_token

router = APIRouter()

@router.get("/health")
async def api_health():
    """프론트에서 서버 상태 확인용."""
    return {"ok": True, "service": "suyatrade_web_rest"}

# --------------------------
# 일반 설정 (웹 대시보드)
# --------------------------
@router.get("/settings/general")
async def get_general_settings():
    data = load_settings()
    return {"status_code": 200, "response": data, "headers": {}}

@router.put("/settings/general")
async def put_general_settings(payload: dict):
    try:
        save_settings(payload)
        return {"status_code": 200, "response": {"ok": True}, "headers": {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "SETTINGS_SAVE_FAILED", "hint": str(e)})

# --------------------------
# 텔레그램 설정 (웹 대시보드)
# --------------------------
@router.get("/settings/telegram")
async def get_telegram_settings():
    data = load_telegram_settings()
    return {"status_code": 200, "response": data, "headers": {}}

@router.put("/settings/telegram")
async def put_telegram_settings(payload: dict):
    try:
        save_telegram_settings(payload)
        return {"status_code": 200, "response": {"ok": True}, "headers": {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "TELEGRAM_SAVE_FAILED", "hint": str(e)})

# --------------------------
# 토큰 발급
# --------------------------
@router.post("/token")
async def api_token_issue():
    """모의서버 액세스 토큰 발급(로컬 전용)."""
    try:
        token = await get_token(debug=False)
        return {"status_code": 200, "response": {"token": token}, "headers": {}}
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": "TOKEN_FETCH_FAILED", "hint": str(e)})

@router.get("/token/debug")
async def api_token_debug():
    """토큰 발급 디버그."""
    token = await get_token(debug=True)
    ok = bool(token)
    return {"ok": ok, "token_prefix": token[:24] + "..." if ok else ""}
