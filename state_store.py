from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


STATE_FILE = Path("state.json")

DEFAULT_STATE: dict[str, Any] = {
    "status": "idle",
    "job": None,
    "logs": [],
    "updated_at": None,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return dict(DEFAULT_STATE)
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_STATE)
    if not isinstance(data, dict):
        return dict(DEFAULT_STATE)

    merged = dict(DEFAULT_STATE)
    merged.update(data)
    if not isinstance(merged.get("logs"), list):
        merged["logs"] = []
    return merged


def save_state(state: dict[str, Any]) -> None:
    state["updated_at"] = now_text()
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_log(message: str) -> None:
    state = load_state()
    logs = state.setdefault("logs", [])
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    state["logs"] = logs[-300:]
    save_state(state)


def start_job(job: dict[str, Any]) -> None:
    state = load_state()
    state["status"] = "running"
    state["job"] = job
    state["logs"] = []
    save_state(state)
    append_log("작업이 시작되었습니다.")


def stop_job() -> None:
    state = load_state()
    state["status"] = "stopped"
    save_state(state)
    append_log("중지 요청을 기록했습니다.")
