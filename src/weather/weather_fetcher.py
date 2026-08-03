"""
기상청 단기예보 API 조회 및 가공 모듈.
- getVilageFcst 호출 → 오늘 하루치 데이터 필터링 → 오전/오후 요약으로 가공.
- 좌표(nx, ny)만 받으면 어느 지역이든 동일하게 작동하는 지역 무관 엔진으로 설계.
  (지역명 → 좌표 변환은 별도 모듈에서 처리 예정, 1-5)
- 오전 데이터는 항상 당일 이른 발표분(05시, 이르면 02시)을 고정 사용하고,
  오후 데이터는 조회 시점 기준 가장 최근 발표분을 사용 (API가 발표시각 이후
  미래 시점만 제공하는 구조적 제약 때문에 이렇게 분리함).
- 강수 표현은 PTY(강수형태)를 1순위로, PTY가 있을 때만 POP(강수확률)으로
  표현 강도를 조절 (POP < 30%: 생략, 30~50%: "올 수 있어요", 50%+: "확실해요").
"""

import os
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote
from dotenv import load_dotenv
from src.weather.region_lookup import get_coordinates

load_dotenv()

API_KEY = unquote(os.getenv("WEATHER_API_KEY"))
BASE_URL = os.getenv("WEATHER_BASE_URL")
URL = f"{BASE_URL}/getVilageFcst"

SKY_MAP = {"1": "맑음", "3": "구름많음", "4": "흐림"}
PTY_MAP = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}

BASE_TIMES = [2, 5, 8, 11, 14, 17, 20, 23]

def _get_base_datetime_for(target_hour: int, now: datetime) -> tuple[str, str]:
    """
    target_hour(0~23) 시각의 날씨 데이터를 포함하는, 가장 최근의 정규 발표시각을 계산.
    - target_hour가 0~4시(자정~05시 이전)면, 전날 23시 발표분 사용
      (해당 시각을 포함하는 당일 발표분이 아직 존재하지 않으므로 — 유일한 예외).
    - 그 외에는, target_hour 이하인 정규 발표시각(02,05,08,11,14,17,20,23) 중
      가장 늦은 것을 사용 (발표시각+1시간부터 데이터가 나오므로, 이렇게 하면
      target_hour 데이터가 반드시 포함됨).
    """
    if target_hour < 5:
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"

    available = [t for t in BASE_TIMES if t <= target_hour]
    base_hour = max(available)
    return now.strftime("%Y%m%d"), f"{base_hour:02d}00"

def fetch_raw_forecast(nx: int, ny: int, base_date: str, base_time: str) -> list[dict]:
    """
    기상청 API를 호출해서 원본 예보 항목(item) 리스트를 그대로 반환.
    nx, ny, base_date, base_time을 파라미터로 받는 순수 호출 함수.
    """
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    response = requests.get(URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    header = data["response"]["header"]
    if header["resultCode"] != "00":
        raise RuntimeError(f"기상청 API 오류: {header['resultMsg']}")

    return data["response"]["body"]["items"]["item"]


def _pick_representative(items: list[dict], today_str: str, start: int, end: int) -> dict:
    """
    items 중 오늘 날짜(today_str) & 지정된 시간 구간(start~end, 양끝 포함)에
    해당하는 SKY/PTY/POP 값을 모아서, 그중 가장 이른 시각을 대표값으로 사용.
    """
    candidates = {}
    for item in items:
        if item["fcstDate"] != today_str:
            continue
        category = item["category"]
        if category not in ("SKY", "PTY", "POP"):
            continue
        fcst_time = int(item["fcstTime"])
        if start <= fcst_time <= end:   # < 에서 <= 로 변경 (경계값 누락 방지)
            candidates.setdefault(fcst_time, {})[category] = item["fcstValue"]

    if not candidates:
        return {"sky": "정보없음", "pty": "정보없음", "pop": None}

    earliest_time = min(candidates.keys())
    values = candidates[earliest_time]
    return {
        "sky": SKY_MAP.get(values.get("SKY"), "정보없음"),
        "pty": PTY_MAP.get(values.get("PTY"), "정보없음"),
        "pop": int(values["POP"]) if "POP" in values else None,
    }


def get_today_weather_summary(nx: int, ny: int, now: datetime = None) -> dict:
    """
    오늘 날짜의 예보 데이터를 오전/오후 요약 형태로 가공.
    - 오전(06~12시) 대표 시각(09시)과 오후(12~24시) 대표 시각(15시)을 기준으로,
      각각 _get_base_datetime_for()를 호출해 적절한 발표분을 계산.
    - 최저기온(tmn): 9시 기준 발표분(morning_items)은 발표시각+1시간 규칙 때문에
      새벽(00~05시대) 데이터를 놓칠 수 있어 실제보다 높게 계산되는 문제가 있었음.
      이를 해결하기 위해 항상 05시 기준 발표분을 별도로 조회해서, 그 안의
      TMP(시간별 기온) 값들 중 최솟값을 tmn으로 사용 (새벽 시간대 포함 보장).
      TMN 카테고리 자체는 당일 값이 API 응답에서 아예 빠지는 경우가 있어 신뢰 불가.
    - 최고기온(tmx): TMX는 당일 값이 안정적으로 제공되어, morning_items에서
      API 값을 그대로 사용.

    Args:
        now: 기준 시각 (기본값 None이면 실제 현재 시각 사용).
             테스트 시 임의의 시각을 주입해서 특정 시간대 케이스를 검증할 수 있음.

    Returns:
        dict: {
            "date": "20260803",
            "tmn": 26, "tmx": 37,
            "morning": {"sky": "구름많음", "pty": "없음", "pop": 20},
            "afternoon": {"sky": "맑음", "pty": "없음", "pop": 0},
        }
    """
    if now is None:
        now = datetime.now()
    today_str = now.strftime("%Y%m%d")

    morning_date, morning_time = _get_base_datetime_for(9, now)
    afternoon_date, afternoon_time = _get_base_datetime_for(15, now)
    tmn_date, tmn_time = _get_base_datetime_for(5, now)

    morning_items = fetch_raw_forecast(nx, ny, morning_date, morning_time)

    if (morning_date, morning_time) == (afternoon_date, afternoon_time):
        afternoon_items = morning_items
    else:
        afternoon_items = fetch_raw_forecast(nx, ny, afternoon_date, afternoon_time)

    if (tmn_date, tmn_time) == (morning_date, morning_time):
        tmn_items = morning_items
    else:
        tmn_items = fetch_raw_forecast(nx, ny, tmn_date, tmn_time)

    tmx = None
    for item in morning_items:
        if item["fcstDate"] != today_str:
            continue
        if item["category"] == "TMX":
            tmx = round(float(item["fcstValue"]))

    tmn = None
    tmn_tmp_values = [
        float(item["fcstValue"])
        for item in tmn_items
        if item["fcstDate"] == today_str and item["category"] == "TMP"
    ]
    if tmn_tmp_values:
        tmn = round(min(tmn_tmp_values))

    morning_summary = _pick_representative(morning_items, today_str, 600, 1200)
    afternoon_summary = _pick_representative(afternoon_items, today_str, 1200, 1800)

    return {
        "date": today_str,
        "tmn": tmn,
        "tmx": tmx,
        "morning": morning_summary,
        "afternoon": afternoon_summary,
    }

def _describe(part: dict) -> str:
    """
    하늘상태 + 강수형태 + 강수확률을 종합해서 자연스러운 문장으로 구성.
    - PTY(강수형태)가 "없음"이면 하늘상태만 표시 (POP과 무관).
    - PTY가 있으면 POP 수치로 표현 강도 조절
      (30% 미만: 언급 생략, 30~50%: "올 수 있어요", 50%+: "확실해요").
    """
    sky, pty, pop = part["sky"], part["pty"], part["pop"]

    if pty in ("없음", "정보없음"):
        return sky

    if pop is None:
        return f"{sky}, {pty} 소식이 있어요"
    elif pop < 30:
        return sky
    elif pop < 50:
        return f"{sky}, {pty}가 올 수 있어요"
    else:
        return f"{sky}, {pty} 소식이 확실해요"


def format_weather_summary(summary: dict) -> str:
    """
    get_today_weather_summary() 결과를 사람이 읽기 좋은 텍스트로 변환.
    """
    date_str = summary['date']
    formatted_date = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:8]}일"

    def _line(label: str, part: dict) -> str:
        desc = _describe(part)
        pop_text = f" (강수확률 {part['pop']}%)" if part["pop"] is not None else ""
        return f"{label}: {desc}{pop_text}"

    lines = [
        f"오늘 날씨 ({formatted_date})",   # summary[...] 없이, 그냥 변수 그대로
        f"최저 {summary['tmn']}°C / 최고 {summary['tmx']}°C",
        _line("오전", summary["morning"]),
        _line("오후", summary["afternoon"]),
    ]
    return "\n".join(lines)

def get_weather_by_region(region_1: str, region_2: str) -> dict:
    """
    지역명(시/도, 구/군)을 받아서 오늘 날씨 요약을 반환하는 최종 진입점 함수.
    region_lookup.py(지역→좌표)와 이 파일의 좌표 기반 엔진을 연결.

    Args:
        region_1: 시/도 (예: "서울특별시")
        region_2: 구/군 (예: "강남구")

    Returns:
        dict: get_today_weather_summary()와 동일한 구조
    """
    nx, ny = get_coordinates(region_1, region_2)
    return get_today_weather_summary(nx, ny)

if __name__ == "__main__":
    TEST_DATE = datetime(2026, 8, 2)  # 테스트 기준 날짜 (이미 지나간 날짜여야 함)

    test_cases = [
        ("자정 직전 (23:59)", TEST_DATE.replace(hour=23, minute=59)),
        ("자정~05시 이전 (02:30)", TEST_DATE.replace(hour=2, minute=30)),
        ("새벽 5시 (05:00)", TEST_DATE.replace(hour=5, minute=0)),
        ("경계값 케이스 (17:00, 발표시각+1시간=18시 경계)", TEST_DATE.replace(hour=17, minute=0)),
        ("일반 케이스 (14:30)", TEST_DATE.replace(hour=14, minute=30)),
    ]

    for label, fake_now in test_cases:
        print(f"\n{'=' * 50}")
        print(f"[테스트] {label}  (기준 시각: {fake_now})")
        print('=' * 50)
        try:
            summary = get_today_weather_summary(nx=61, ny=126, now=fake_now)
            print(summary)
            print()
            print(format_weather_summary(summary))
        except Exception as e:
            print(f"에러 발생: {e}")