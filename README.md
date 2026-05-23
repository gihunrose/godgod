# KTXgo Streamlit Server

휴대폰 브라우저에서 접속하는 KTXgo 서버 제어판입니다.

이 버전은 Streamlit Cloud에서 조건을 저장하고, 별도 브라우저 엔진 서버에 작업을 전달합니다. 결제 자동화는 포함하지 않습니다.

## GitHub에 올릴 파일

`streamlit_server` 폴더 안의 파일을 GitHub repo 루트에 올립니다.

- `app.py`
- `browser_engine_client.py`
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
ENGINE_MODE = "browser"
BROWSER_ENGINE_URL = "http://YOUR_VM_PUBLIC_IP:8787"
BROWSER_ENGINE_TOKEN = "브라우저-엔진-토큰"
BROWSER_ENGINE_TIMEOUT_SECONDS = "60"
```

직접 API 방식은 코레일 `MACRO ERROR`로 막힐 수 있어 기본값에서 제외했습니다. 그래도 테스트용으로 직접 API 모드를 켜려면 아래 값을 추가하고 `ENGINE_MODE = "direct_api"`로 바꿉니다.

```toml
KTX_ID = "코레일-멤버십번호"
KTX_PASSWORD = "코레일-비밀번호"
KORAIL_TIMEOUT_SECONDS = "40"
```

절대 GitHub 파일에 코레일 계정 정보를 직접 적지 마세요.

## 사용 순서

1. `browser_engine_server`를 Oracle VM 같은 별도 서버에서 실행합니다.
2. Streamlit Cloud Secrets에 `BROWSER_ENGINE_URL`, `BROWSER_ENGINE_TOKEN`을 설정합니다.
3. Streamlit Cloud에 다시 배포합니다.
4. PIN으로 입장합니다.
5. 조건을 저장하고 `1회 테스트`를 눌러 브라우저 엔진 연결을 확인합니다.

## 중요한 제한

코레일이 `MACRO ERROR` 또는 최신 앱 업데이트 안내로 자동 접속을 차단하면 앱 로그에 그대로 표시하고 반복을 멈춥니다. 이 프로젝트에는 차단 우회, 토큰 복제, 브라우저 지문 위장 같은 로직을 넣지 않습니다.

`TIMEOUT` 또는 `NETWORK` 오류는 브라우저 엔진 서버 연결 문제, 코레일 응답 지연, Streamlit Cloud의 외부 접속 경로 문제 때문에 생길 수 있습니다. 이 오류가 3회 연속 발생하면 앱은 자동으로 중지됩니다.

Streamlit Community Cloud는 무료 서버라서 장시간 실행이 항상 보장되지는 않습니다. 실제 사용 전에는 짧은 조건으로 `1회 테스트`를 먼저 확인하세요.
