# backend/app/main.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from .config import settings

app = FastAPI(
    title="Suyatrade Web (Mock REST)",
    version="1.0.0",
)

# CORS (개발 중 편하게 모두 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 필요하면 127.0.0.1만 허용하도록 좁혀도 됨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /web 정적 파일 마운트 (프로젝트 루트의 web 폴더)
# app/app.py 기준으로 상위 상위가 프로젝트 루트
WEB_DIR = (Path(__file__).resolve().parents[2] / "web")
app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

@app.get("/", include_in_schema=False)
async def _root():
    # 루트 접근 시 UI로 보냄
    return RedirectResponse(url="/web/")

# ---- 라우터 붙이기 ----
# (settings/telegram, token/health 등 잡무 라우트)
from .routes_misc import router as misc_router
app.include_router(misc_router)

# (계좌 요약 라우트) - 지금 404 원인: 이게 빠져있었음
from .routes_account import router as account_router
app.include_router(account_router)

# (주문 라우트가 있다면 붙임: 없으면 무시)
try:
    from .routes_orders import router as orders_router
    app.include_router(orders_router)
except Exception:
    pass

# 헬스엔드포인트 (프론트 상단 '서버 상태' 버튼용)
@app.get("/api/health")
async def health():
    return {"status": "ok", "base_url": settings.base_url}
