# backend/app/routes_orders.py
from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from .kiwoom import order_cash

router = APIRouter()


class OrderReq(BaseModel):
    code: str = Field(..., description="종목코드(6자리)")
    qty: int = Field(..., gt=0, description="수량")
    market: bool = Field(True, description="True=시장가, False=지정가")
    price: int | None = Field(0, description="지정가일 때만 사용")


@router.post("/orders/stock/buy")
async def order_buy(req: OrderReq, x_idempotency_key: str | None = Header(default=None)):
    status, body, headers = await order_cash(
        req.code, req.qty, True, req.market, req.price or 0, x_idempotency_key
    )
    return {"status_code": status, "response": body, "headers": headers}


@router.post("/orders/stock/sell")
async def order_sell(req: OrderReq, x_idempotency_key: str | None = Header(default=None)):
    status, body, headers = await order_cash(
        req.code, req.qty, False, req.market, req.price or 0, x_idempotency_key
    )
    return {"status_code": status, "response": body, "headers": headers}
