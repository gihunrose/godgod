from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import requests
from urllib3.exceptions import InsecureRequestWarning


warnings.simplefilter("ignore", InsecureRequestWarning)


class KorailClientError(RuntimeError):
    def __init__(self, message: str, code: str = "") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Train:
    train_no: str
    train_type: str
    dep_time: str
    arr_time: str
    general_seat: str
    special_seat: str
    raw: dict[str, str]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Train":
        raw = {str(k): "" if v is None else str(v) for k, v in row.items()}
        return cls(
            train_no=raw.get("h_trn_no", ""),
            train_type=raw.get("h_car_tp_nm", "") or raw.get("h_trn_clsf_nm", ""),
            dep_time=raw.get("h_dpt_tm_qb", ""),
            arr_time=raw.get("h_arv_tm_qb", ""),
            general_seat=raw.get("h_gen_rsv_nm", ""),
            special_seat=raw.get("h_spe_rsv_nm", ""),
            raw=raw,
        )

    def summary(self) -> str:
        dep = self.dep_time[:4] if self.dep_time else "----"
        arr = self.arr_time[:4] if self.arr_time else "----"
        return (
            f"{self.train_no}호 {dep}->{arr} "
            f"일반:{self.general_seat or '-'} 특실:{self.special_seat or '-'}"
        )

    @property
    def dep_date(self) -> str:
        return self.raw.get("h_dpt_dt", "")

    @property
    def train_cls_cd(self) -> str:
        code = self.raw.get("h_trn_clsf_cd", "")
        if code:
            return code
        if "ITX" in self.train_type.upper():
            return "101"
        return "100"

    @property
    def has_general(self) -> bool:
        code = self.raw.get("h_gen_rsv_cd", "")
        return code == "11" or "예약" in self.general_seat or "좌석" in self.general_seat

    @property
    def has_special(self) -> bool:
        code = self.raw.get("h_spe_rsv_cd", "")
        return code == "11" or "예약" in self.special_seat or "좌석" in self.special_seat


class KorailSearchClient:
    """Small Korail mobile-web client for basic login and timetable checks.

    This does not include anti-bot bypass logic. If Korail rejects the request,
    the caller receives the official error message so the app can surface it.
    """

    _DEVICE = "AD"
    _VERSION = "250601002"
    _KEY = "korail1234567890"

    LOGIN_URL = "https://smart.letskorail.com/classes/com.korail.mobile.login.Login"
    SCHEDULE_URL = "https://smart.letskorail.com/classes/com.korail.mobile.seatMovie.ScheduleView"
    RESERVE_URL = "https://smart.letskorail.com/classes/com.korail.mobile.certification.TicketReservation"

    def __init__(self, member_id: str, password: str, timeout_seconds: int = 25) -> None:
        self.member_id = member_id.strip()
        self.password = password.strip()
        self.timeout_seconds = max(5, min(int(timeout_seconds), 60))
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update(
            {
                "User-Agent": (
                    "Dalvik/2.1.0 (Linux; U; Android 11; "
                    "SM-G998N Build/RP1A.200720.012)"
                ),
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    def _base_params(self) -> dict[str, str]:
        return {"Device": self._DEVICE, "Version": self._VERSION, "Key": self._KEY}

    def _post_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.session.post(url, data=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.Timeout as exc:
            raise KorailClientError("코레일 응답 시간이 초과되었습니다.", "TIMEOUT") from exc
        except requests.exceptions.RequestException as exc:
            raise KorailClientError(f"코레일 접속 실패: {exc}", "NETWORK") from exc
        except ValueError as exc:
            raise KorailClientError("코레일 응답을 JSON으로 해석하지 못했습니다.", "BAD_JSON") from exc

        if str(payload.get("strResult", "")).upper() == "FAIL":
            message = str(payload.get("h_msg_txt", "API 처리 실패"))
            code = str(payload.get("h_msg_cd", "FAIL"))
            raise KorailClientError(message, code)
        return payload

    def login(self) -> None:
        params = self._base_params()
        params.update(
            {
                "txtMemberNo": self.member_id,
                "txtPwd": self.password,
                "txtInputFlg": "1",
            }
        )
        payload = self._post_json(self.LOGIN_URL, params)
        result = str(payload.get("strResult", "")).upper()
        if result not in {"SUCC", "SUCCESS", "Y", "1"}:
            message = str(payload.get("h_msg_txt", "로그인 실패"))
            code = str(payload.get("h_msg_cd", result or "LOGIN_FAIL"))
            raise KorailClientError(message, code)

    def search(self, dep: str, arr: str, ride_date: str, hour: str, adults: int) -> list[Train]:
        params = self._base_params()
        params.update(
            {
                "radJobId": "1",
                "selGoTrain": "00",
                "txtGoAbrdDt": ride_date,
                "txtGoEnd": arr,
                "txtGoHour": f"{hour.zfill(2)}0000",
                "txtGoStart": dep,
                "txtMenuId": "11",
                "txtPsgFlg_1": str(adults),
                "txtTrnGpCd": "00",
            }
        )
        payload = self._post_json(self.SCHEDULE_URL, params)
        infos = payload.get("trn_infos", {})
        if not isinstance(infos, dict):
            return []

        rows = infos.get("trn_info", [])
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            return []

        return [Train.from_row(row) for row in rows if isinstance(row, dict)]

    def reserve(self, train: Train, seat_type: str, adults: int) -> dict[str, Any]:
        params = self._base_params()
        params.update(
            {
                "txtMenuId": "11",
                "txtJobId": "1101",
                "txtTotPsgCnt": str(adults),
                "txtJrnyCnt": "1",
                "txtJrnySqno1": "001",
                "txtJrnyTpCd1": "11",
                "txtDptDt1": train.dep_date,
                "txtDptRsStnCd1": train.raw.get("h_dpt_rs_stn_cd", ""),
                "txtDptTim1": train.dep_time,
                "txtArvRsStnCd1": train.raw.get("h_arv_rs_stn_cd", ""),
                "txtTrnNo1": train.train_no,
                "txtRunDt1": train.dep_date,
                "txtTrnClsfCd1": train.train_cls_cd,
                "txtPsrmClCd1": "1" if seat_type == "general" else "2",
                "txtPsgTpCd1": "1",
                "txtDiscKndCd1": "000",
                "txtCompaCnt1": str(adults),
            }
        )
        return self._post_json(self.RESERVE_URL, params)
