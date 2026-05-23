# KTXgo Streamlit Server

휴대폰에서 접속할 서버형 제어판입니다. 첫 단계는 Streamlit Cloud 배포와 모바일 UI 검증입니다.

## GitHub에 올릴 파일

이 `streamlit_server` 폴더 안의 파일을 새 GitHub repo 루트에 올립니다.

- `app.py`
- `reservation_engine.py`
- `state_store.py`
- `requirements.txt`
- `.gitignore`

## Streamlit Secrets

Streamlit Community Cloud 앱 설정의 **Secrets**에 아래 값을 넣습니다.

```toml
APP_PIN = "원하는-접속-핀"
```

나중에 알림/예약 백엔드를 붙일 때 아래 값을 추가할 수 있습니다.

```toml
KTX_ID = ""
KTX_PASSWORD = ""
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
```

## 배포 순서

1. GitHub에서 새 repository를 만듭니다.
2. 이 폴더의 파일을 repository 루트에 업로드합니다.
3. Streamlit Community Cloud에서 **New app**을 누릅니다.
4. 방금 만든 repository를 선택합니다.
5. Main file path에 `app.py`를 입력합니다.
6. Advanced settings 또는 앱 Settings에서 Secrets에 `APP_PIN`을 설정합니다.
7. Deploy를 누릅니다.

## 현재 상태

현재 버전은 자동 예매 엔진을 연결하지 않은 1차 서버입니다.

- 조건 저장
- 시작/중지 상태 저장
- 로그 표시
- PIN 보호

실제 예약 엔진은 `reservation_engine.py`의 `ReservationEngine.run_once()` 뒤에 붙입니다.
코레일 anti-bot 차단을 우회하는 로직은 포함하지 않습니다.
