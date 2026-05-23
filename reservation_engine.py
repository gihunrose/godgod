from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from browser_engine_client import BrowserEngineClient, BrowserEngineClientError
from korail_search_client import KorailClientError, KorailSearchClient, Train
from server_config import get_secret
from state_store import append_log


@dataclass(frozen=True)
class EngineResult:
    ok: bool
    message: str
    reservation_no: str = ""
    fatal: bool = False
    transient: bool = False


def _seat_candidates(seat_mode: str) -> list[str]:
    if seat_mode == "일반실만":
        return ["general"]
    if seat_mode == "특실만":
        return ["special"]
    if seat_mode == "특실 우선":
        return ["special", "general"]
    return ["general", "special"]


def _available_seat(train: Train, seat_mode: str) -> str | None:
    for seat_type in _seat_candidates(seat_mode):
        if seat_type == "general" and train.has_general:
            return "general"
        if seat_type == "special" and train.has_special:
            return "special"
    return None


def _seat_label(seat_type: str) -> str:
    return "일반실" if seat_type == "general" else "특실"


def _matches_train_no(train: Train, wanted: str) -> bool:
    wanted = wanted.strip()
    if not wanted or wanted == "전체":
        return True
    return train.train_no == wanted.replace("호", "").strip()


def _blocked_message(exc: KorailClientError) -> str:
    code = exc.code.upper()
    message = str(exc)
    if code == "MACRO ERROR" or "최신 버전" in message or "안정적인 환경" in message:
        return (
            "코레일이 자동 접속을 차단했습니다. "
            "이 서버 버전은 차단 우회 로직을 넣지 않고 공식 응답을 그대로 표시합니다."
        )
    return ""


def _int_secret(name: str, default: int, min_value: int, max_value: int) -> int:
    value = get_secret(name, "")
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(min_value, min(parsed, max_value))


class ReservationEngine:
    def run_once(self, job: dict[str, Any]) -> EngineResult:
        mode = get_secret("ENGINE_MODE", "browser").lower()
        if mode in {"browser", "browser_server", "remote_browser"}:
            return BrowserServerReservationEngine().run_once(job)
        if mode in {"api", "direct_api", "korail_api"}:
            return DirectApiReservationEngine().run_once(job)
        return EngineResult(
            ok=False,
            message=f"알 수 없는 ENGINE_MODE입니다: {mode}",
            fatal=True,
        )


class BrowserServerReservationEngine:
    def run_once(self, job: dict[str, Any]) -> EngineResult:
        base_url = get_secret("BROWSER_ENGINE_URL")
        token = get_secret("BROWSER_ENGINE_TOKEN")
        if not base_url or not token:
            return EngineResult(
                ok=False,
                message=(
                    "브라우저 엔진이 아직 연결되지 않았습니다. "
                    "Streamlit Secrets에 BROWSER_ENGINE_URL과 BROWSER_ENGINE_TOKEN을 설정하세요."
                ),
                fatal=True,
            )

        timeout_seconds = _int_secret("BROWSER_ENGINE_TIMEOUT_SECONDS", 45, 5, 120)
        append_log("브라우저 엔진에 작업을 전달합니다.")
        client = BrowserEngineClient(base_url, token, timeout_seconds)
        try:
            result = client.run_once(job)
        except BrowserEngineClientError as exc:
            return EngineResult(
                ok=False,
                message=str(exc),
                transient=exc.transient,
            )

        return EngineResult(
            ok=result.ok,
            message=result.message,
            reservation_no=result.reservation_no,
            fatal=result.fatal,
            transient=result.transient,
        )


class DirectApiReservationEngine:
    """Login, search, and optionally reserve without payment automation."""

    def run_once(self, job: dict[str, Any]) -> EngineResult:
        member_id = get_secret("KTX_ID")
        password = get_secret("KTX_PASSWORD")
        if not member_id or not password:
            return EngineResult(
                ok=False,
                message="Streamlit Secrets에 KTX_ID와 KTX_PASSWORD를 설정해야 합니다.",
                fatal=True,
            )

        dep = str(job["dep"])
        arr = str(job["arr"])
        ride_date = str(job["date"])
        hour = str(job["hour"])
        adults = int(job["adults"])
        seat_mode = str(job["seat_mode"])
        train_no = str(job.get("train_no", "전체"))
        reserve_enabled = bool(job.get("reserve_enabled", False))

        timeout_seconds = _int_secret("KORAIL_TIMEOUT_SECONDS", 25, 5, 60)
        append_log(f"코레일 로그인 시도: {member_id[:3]}***")
        client = KorailSearchClient(member_id, password, timeout_seconds=timeout_seconds)

        try:
            client.login()
            append_log("코레일 로그인 성공")
            trains = client.search(dep, arr, ride_date, hour, adults)
        except KorailClientError as exc:
            blocked = _blocked_message(exc)
            if blocked:
                append_log(blocked)
            return EngineResult(
                False,
                f"코레일 요청 실패 [{exc.code}]: {exc}",
                fatal=bool(blocked),
                transient=exc.code.upper() in {"TIMEOUT", "NETWORK"},
            )

        append_log(
            f"조건 확인: {dep}->{arr} {ride_date} {hour}시 이후, "
            f"{adults}명, {seat_mode}, 열차 {train_no}"
        )
        append_log(f"조회 결과: {len(trains)}편")

        if trains:
            for train in trains[:5]:
                append_log(f"조회 열차: {train.summary()}")

        selected: tuple[Train, str] | None = None
        for train in trains:
            if not _matches_train_no(train, train_no):
                continue
            seat_type = _available_seat(train, seat_mode)
            if seat_type:
                selected = (train, seat_type)
                break

        if selected is None:
            return EngineResult(False, "조건에 맞는 예약 가능 좌석을 아직 찾지 못했습니다.")

        train, seat_type = selected
        append_log(f"예약 가능 후보 발견: {train.summary()} / {_seat_label(seat_type)}")

        if not reserve_enabled:
            return EngineResult(
                ok=False,
                message="예약 가능 후보가 있지만 '좌석 발견 시 예약 시도'가 꺼져 있습니다.",
            )

        try:
            reserve_result = client.reserve(train, seat_type, adults)
        except KorailClientError as exc:
            blocked = _blocked_message(exc)
            if blocked:
                append_log(blocked)
            return EngineResult(
                False,
                f"예약 요청 실패 [{exc.code}]: {exc}",
                fatal=bool(blocked),
                transient=exc.code.upper() in {"TIMEOUT", "NETWORK"},
            )

        reservation_no = str(reserve_result.get("h_pnr_no", ""))
        append_log(
            f"예약 요청 성공: {train.train_no}호 {_seat_label(seat_type)} "
            f"예약번호 {reservation_no or '응답에서 미확인'}"
        )
        return EngineResult(
            ok=True,
            message="예약 요청이 성공했습니다. 코레일 공식 앱/웹에서 결제를 완료하세요.",
            reservation_no=reservation_no,
        )
