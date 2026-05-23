from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from reservation_engine import ReservationEngine
from state_store import append_log, load_state, save_state, start_job, stop_job


STATIONS = [
    "서울",
    "용산",
    "영등포",
    "광명",
    "행신",
    "수원",
    "평택지제",
    "천안아산",
    "오송",
    "대전",
    "서대전",
    "익산",
    "정읍",
    "광주송정",
    "나주",
    "목포",
    "전주",
    "순천",
    "여수엑스포",
    "김천구미",
    "동대구",
    "서대구",
    "신경주",
    "밀양",
    "구포",
    "부산",
    "울산(통도사)",
    "마산",
    "창원",
    "창원중앙",
    "진주",
    "포항",
    "강릉",
    "동해",
]

SEAT_MODES = ["일반실 우선", "일반실만", "특실 우선", "특실만"]


def require_pin() -> bool:
    app_pin = str(st.secrets.get("APP_PIN", "")).strip()
    if not app_pin:
        st.error("Streamlit Secrets에 APP_PIN을 먼저 설정하세요.")
        return False

    with st.form("pin_form"):
        pin = st.text_input("접속 PIN", type="password")
        submitted = st.form_submit_button("입장")

    if submitted and pin == app_pin:
        st.session_state["authed"] = True

    if not st.session_state.get("authed"):
        st.info("개인 예약 정보 보호를 위해 PIN이 필요합니다.")
        return False
    return True


def make_job() -> dict[str, Any] | None:
    with st.form("job_form"):
        col1, col2 = st.columns(2)
        with col1:
            dep = st.selectbox("출발역", STATIONS, index=STATIONS.index("광명"))
            ride_date = st.date_input("탑승일", value=date.today())
            adults = st.number_input("성인", min_value=1, max_value=9, value=1, step=1)
        with col2:
            arr = st.selectbox("도착역", STATIONS, index=STATIONS.index("부산"))
            hour = st.selectbox("출발 시각 이후", [f"{i:02d}" for i in range(24)])
            seat_mode = st.selectbox("좌석", SEAT_MODES)

        train_no = st.text_input("특정 열차 번호", placeholder="비우면 전체 조회")
        submitted = st.form_submit_button("조건 저장")

    if not submitted:
        return None

    if dep == arr:
        st.error("출발역과 도착역은 달라야 합니다.")
        return None

    return {
        "dep": dep,
        "arr": arr,
        "date": ride_date.strftime("%Y%m%d"),
        "hour": hour,
        "adults": int(adults),
        "seat_mode": seat_mode,
        "train_no": train_no.strip() or "전체",
    }


def render_status() -> None:
    state = load_state()
    status = state.get("status", "idle")
    st.subheader("상태")

    if status == "running":
        st.success("실행 중")
    elif status == "stopped":
        st.warning("중지됨")
    elif status == "success":
        st.success("예약 성공")
    elif status == "error":
        st.error("오류")
    else:
        st.info("대기 중")

    job = state.get("job")
    if isinstance(job, dict):
        st.json(job, expanded=False)

    logs = state.get("logs", [])
    st.subheader("로그")
    if logs:
        st.code("\n".join(logs[-120:]), language="text")
    else:
        st.caption("아직 로그가 없습니다.")


def main() -> None:
    st.set_page_config(page_title="KTXgo Server", page_icon="🚄", layout="centered")
    st.title("KTXgo 서버 제어판")

    if not require_pin():
        return

    job = make_job()
    if job:
        state = load_state()
        state["job"] = job
        save_state(state)
        append_log("조건이 저장되었습니다.")
        st.success("조건을 저장했습니다.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("시작", use_container_width=True):
            state = load_state()
            job = state.get("job")
            if not isinstance(job, dict):
                st.error("먼저 조건을 저장하세요.")
            else:
                start_job(job)
                st.rerun()

    with col2:
        if st.button("1회 테스트", use_container_width=True):
            state = load_state()
            job = state.get("job")
            if not isinstance(job, dict):
                st.error("먼저 조건을 저장하세요.")
            else:
                result = ReservationEngine().run_once(job)
                append_log(result.message)
                st.rerun()

    with col3:
        if st.button("중지", use_container_width=True):
            stop_job()
            st.rerun()

    render_status()


if __name__ == "__main__":
    main()
