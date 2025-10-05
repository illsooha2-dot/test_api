import sys, requests, uuid, json
from pathlib import Path
CUR = Path(__file__).resolve()
BACKEND = CUR.parents[1] / "backend"
sys.path.insert(0, str(BACKEND))
API = "http://127.0.0.1:5174"

def idem(): return str(uuid.uuid4())

def post_buy(code="005930", qty=1, market=True, price=0):
    url = f"{API}/api/orders/stock/buy"
    body = {"code": code, "qty": qty, "market": market, "price": price}
    headers = {"Content-Type":"application/json", "X-Idempotency-Key": idem()}
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
    print("RESP:", r.json())
    print("HEAD:", dict(r.headers))

if __name__ == "__main__":
    post_buy()
