from __future__ import annotations

import threading
import time

from reservation_engine import ReservationEngine
from state_store import append_log, load_state, save_state


_WORKER_THREAD: threading.Thread | None = None
_WORKER_LOCK = threading.Lock()


def worker_is_alive() -> bool:
    return _WORKER_THREAD is not None and _WORKER_THREAD.is_alive()


def ensure_worker_started() -> bool:
    global _WORKER_THREAD

    with _WORKER_LOCK:
        if worker_is_alive():
            return False

        _WORKER_THREAD = threading.Thread(target=_worker_main, daemon=True)
        _WORKER_THREAD.start()
        return True


def _worker_main() -> None:
    append_log("백그라운드 작업 루프가 켜졌습니다.")
    engine = ReservationEngine()

    while True:
        state = load_state()
        status = state.get("status")
        job = state.get("job")

        if status != "running":
            append_log("작업 상태가 running이 아니어서 루프를 종료합니다.")
            return
        if not isinstance(job, dict):
            state["status"] = "error"
            save_state(state)
            append_log("작업 조건이 없어 루프를 종료합니다.")
            return

        result = engine.run_once(job)
        if result.ok:
            state = load_state()
            state["status"] = "success"
            state["reservation_no"] = result.reservation_no
            save_state(state)
            append_log(result.message)
            return

        if result.fatal:
            state = load_state()
            state["status"] = "error"
            save_state(state)
            append_log(f"반복을 중지합니다. {result.message}")
            return

        append_log(f"아직 성공하지 못했습니다. {result.message}")
        time.sleep(int(job.get("poll_interval", 30)))
