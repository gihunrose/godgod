# KTXgo Streamlit Server

휴대폰 브라우저에서 접속하는 KTXgo 서버 제어판입니다.

이 버전은 Streamlit Cloud에서 조건을 저장하고, 서버가 주기적으로 코레일 로그인/시간표 조회를 시도합니다. 결제 자동화는 포함하지 않습니다. 화면에서 `좌석 발견 시 예약 시도`를 체크한 경우에만 결제 전 예약 요청까지 시도합니다.

## GitHub에 올릴 파일

`streamlit_server` 폴더 안의 파일을 GitHub repo 루트에 올립니다.

- `app.py`
- `korail_search_client.py`
- `reservation_engine.py`
- `server_config.py`
- `state_store.py`
- `worker.py`
- `requirements.txt`
- `.gitignore`

## Streamlit Secrets

Streamlit Community Cloud의 앱 설정에서 **Secrets**에 아래 값을 넣습니다.

```toml
APP_PIN = "원하는-접속-PIN"
KTX_ID = "코레일-멤버십번호"
KTX_PASSWORD = "코레일-비밀번호"
```

절대 GitHub 파일에 코레일 계정 정보를 직접 적지 마세요.

## 사용 순서

1. Streamlit Cloud에 다시 배포합니다.
2. PIN으로 입장합니다.
3. 출발역, 도착역, 탑승일, 시간, 좌석 조건을 저장합니다.
4. 처음에는 `좌석 발견 시 예약 시도`를 끄고 `1회 테스트`를 눌러 로그인/조회가 되는지 봅니다.
5. 조회가 정상이고 예약까지 맡길 때만 체크를 켠 뒤 `시작`을 누릅니다.
6. 예약 성공 로그가 뜨면 코레일 공식 앱/웹에서 결제를 완료합니다.

## 중요한 제한

코레일이 `MACRO ERROR` 또는 최신 앱 업데이트 안내로 자동 접속을 차단하면 앱 로그에 그대로 표시합니다. 이 프로젝트에는 차단 우회, 토큰 복제, 브라우저 지문 위장 같은 로직을 넣지 않습니다.

Streamlit Community Cloud는 무료 서버라서 장시간 실행이 항상 보장되지는 않습니다. 실제 사용 전에는 짧은 조건으로 `1회 테스트`를 먼저 확인하세요.
