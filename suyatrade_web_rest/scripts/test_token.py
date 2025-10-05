import requests

API = "http://127.0.0.1:5174"

def main():
    try:
        r = requests.post(f"{API}/api/token", timeout=10)
        if r.ok:
            token = r.json().get("token", "")
            print("TOKEN:", (token[:24] + "...") if token else "<empty>")
            print("BASE_URL:", requests.get(f"{API}/api/health", timeout=5).json().get("base_url"))
            return
    except Exception as e:
        print("Error calling /api/token:", e)

    print("\n[!] 토큰 실패 — 상세 이유 확인")
    try:
        dbg = requests.post(f"{API}/api/token/debug", timeout=15).json()
        for i, a in enumerate(dbg.get("attempts", []), 1):
            print(f" {i}. url={a.get('url')} kind={a.get('kind')} status={a.get('status')}")
            print("    body:", a.get("body") or a.get("error"))
    except Exception as e:
        print("Error calling /api/token/debug:", e)

if __name__ == "__main__":
    main()
