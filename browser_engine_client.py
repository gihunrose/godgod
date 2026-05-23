from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class BrowserEngineClientError(RuntimeError):
    def __init__(self, message: str, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


@dataclass(frozen=True)
class BrowserEngineResponse:
    ok: bool
    message: str
    reservation_no: str = ""
    fatal: bool = False
    transient: bool = False


class BrowserEngineClient:
    def __init__(self, base_url: str, token: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = max(5, min(int(timeout_seconds), 120))

    def run_once(self, job: dict[str, Any]) -> BrowserEngineResponse:
        try:
            response = requests.post(
                f"{self.base_url}/run-once",
                json={"job": job},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.Timeout as exc:
            raise BrowserEngineClientError("브라우저 엔진 응답 시간이 초과되었습니다.", transient=True) from exc
        except requests.exceptions.RequestException as exc:
            raise BrowserEngineClientError(f"브라우저 엔진 접속 실패: {exc}", transient=True) from exc
        except ValueError as exc:
            raise BrowserEngineClientError("브라우저 엔진 응답을 해석하지 못했습니다.") from exc

        return BrowserEngineResponse(
            ok=bool(payload.get("ok", False)),
            message=str(payload.get("message", "")),
            reservation_no=str(payload.get("reservation_no", "")),
            fatal=bool(payload.get("fatal", False)),
            transient=bool(payload.get("transient", False)),
        )
