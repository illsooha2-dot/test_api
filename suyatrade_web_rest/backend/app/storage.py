# backend/app/storage.py
from __future__ import annotations
from pathlib import Path
import json

# 저장 위치: 프로젝트 루트의 data 폴더 (없으면 자동 생성)
_THIS = Path(__file__).resolve()
_ROOT = _THIS.parents[2]              # D:\suyatrade_web_rest
_DATA_DIR = _ROOT / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = _DATA_DIR / "general_settings.json"
TELEGRAM_FILE = _DATA_DIR / "telegram_settings.json"

_DEFAULTS_GENERAL = {
    "layout": "layout3",
    "theme": "dark",
    "order_default_market": True,   # UI에서 시장가 기본값
}

_DEFAULTS_TELEGRAM = {
    "enabled": False,
    "token": "",
    "chat_id": "",
}

def _safe_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

# -----------------------
# General Settings (웹)
# -----------------------
def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return dict(_DEFAULTS_GENERAL)
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _DEFAULTS_GENERAL.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(_DEFAULTS_GENERAL)

def save_settings(payload: dict) -> None:
    data = dict(_DEFAULTS_GENERAL)
    if isinstance(payload, dict):
        data.update(payload)
    _safe_write_json(SETTINGS_FILE, data)

# -----------------------
# Telegram Settings (웹)
# -----------------------
def load_telegram_settings() -> dict:
    if not TELEGRAM_FILE.exists():
        return dict(_DEFAULTS_TELEGRAM)
    try:
        with TELEGRAM_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _DEFAULTS_TELEGRAM.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(_DEFAULTS_TELEGRAM)

def save_telegram_settings(payload: dict) -> None:
    data = dict(_DEFAULTS_TELEGRAM)
    if isinstance(payload, dict):
        # 불필요한 키 제거 & 타입 정리
        data["enabled"] = bool(payload.get("enabled", False))
        data["token"] = str(payload.get("token", "") or "")
        data["chat_id"] = str(payload.get("chat_id", "") or "")
    _safe_write_json(TELEGRAM_FILE, data)
