# 수야 REST 자동매매 (모의: Kiwoom REST)

모의 엔드포인트: https://mockapi.kiwoom.com

## 구조
```
suyatrade_web_rest/
├─ backend/
│  ├─ app/              # FastAPI 백엔드
│  ├─ data/             # 설정 저장(JSON)
│  └─ requirements.txt
├─ scripts/             # 테스트 스크립트
└─ web/                 # 대시보드 UI
```

## 실행 순서 (로컬1/2/3)
### 로컬1: 프로젝트 열기
압축 해제 폴더를 IDE(차이참)로 열기.

### 로컬2: 백엔드 실행
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5174 --reload
```

### 로컬3: 테스트 스크립트
```
cd scripts
python test_token.py   # 토큰 앞 24자리 출력되면 OK
python smoke_buy.py    # 모의 매수 (주말이면 RC4010 응답 정상)
```

### 웹 UI
브라우저: http://127.0.0.1:5174/web/?v=layout3

## 환경변수 (.env)
`backend/.env`에 모의 키 세팅(동봉됨, 테스트 끝나면 교체/폐기):
```
MOCK_BASE_URL=https://mockapi.kiwoom.com
APP_KEY=G0U_V2K7-LV4CXZ3_903ppdMU3vX0guAi4c4hEhKyDU
APP_SECRET=aw7_q_tUII1TqsDEMWkFwdKhVSHUJGn9KP4HgRUoUOo
ACCOUNT_NO=81109460
ACNT_PRDT_CD=01
DEBUG=1
```

## 참고
- 주문 본문은 `ORD_QTY`/`ORD_UNPR` **문자열**로 전송하도록 구현됨.
- 주말/휴장 시간엔 `RC4010: 영업일 아님` 응답이 올 수 있으며 정상 동작입니다.
