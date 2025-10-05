# D:\suyatrade_web_rest\scripts\smoke_limit_buy.py
import requests

API = "http://127.0.0.1:5174"

def call(path, payload):
    r = requests.post(f"{API}{path}", json=payload, timeout=10)
    try:
        print("RESP:", r.json())
    except Exception:
        print("RESP(text):", r.text)
    print("HEAD:", dict(r.headers))

if __name__ == "__main__":
    # 지정가: market=False, price 필수 (문자열로 전송되도록 백엔드에서 처리됨)
    payload = {"code": "005930", "qty": 1, "market": False, "price": 65000}
    call("/api/orders/stock/buy", payload)
