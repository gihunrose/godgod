from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from state_store import append_log


@dataclass(frozen=True)
class EngineResult:
    ok: bool
    message: str
    reservation_no: str = ""


class ReservationEngine:
    """Boundary for the real reservation backend.

    This first Streamlit version intentionally does not include anti-bot bypass
    logic. Keep the UI/server plumbing separate so a compliant backend can be
    plugged in later without rewriting the app.
    """

    def run_once(self, job: dict[str, Any]) -> EngineResult:
        append_log(
            "예약 엔진은 아직 연결되지 않았습니다. "
            "현재 단계는 Streamlit 배포와 모바일 제어 화면 검증입니다."
        )
        append_log(
            f"조건 확인: {job['dep']}->{job['arr']} "
            f"{job['date']} {job['hour']}시, {job['adults']}명, {job['seat_mode']}"
        )
        return EngineResult(
            ok=False,
            message="예약 엔진 미연결: 배포 검증 후 서버 백엔드를 연결해야 합니다.",
        )
