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
ULTRA_SHORT_URL = f"{BASE_URL}/getUltraSrtFcst"

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

def _merge_forecast_items(priority_items: list[dict], fallback_items: list[dict]) -> list[dict]:
    """
    두 예보 데이터 리스트를 하나로 합침.
    같은 (fcstDate, fcstTime, category) 조합이 양쪽에 모두 있으면
    priority_items(초단기)의 값으로 덮어써서, 초단기 우선 원칙을 적용.
    """
    merged = {}
    for item in fallback_items:
        key = (item["fcstDate"], item["fcstTime"], item["category"])
        merged[key] = item
    for item in priority_items:
        key = (item["fcstDate"], item["fcstTime"], item["category"])
        merged[key] = item  # 우선순위: 초단기가 있으면 무조건 덮어씀

    return list(merged.values())

def _pick_representative(items: list[dict], today_str: str, start: int, end: int) -> dict:
    """
    items 중 오늘 날짜(today_str) & 지정된 시간 구간(start~end, 양끝 포함)에
    해당하는 SKY/PTY/POP 값을 모아서 대표값을 뽑음.

    우선순위 (9-3 규칙):
    1순위: 소나기(PTY=4)가 하나라도 있으면 무조건 그 시각을 대표값으로 채택
    2순위: 그 외 강수(PTY≠0)이고 강수확률(POP)이 40% 이상인 시각이 있으면 채택
    3순위: 위 조건에 해당하는 게 없으면(전체가 맑거나 확률 낮음) 가장 이른 시각 채택
    """
    candidates = {}
    for item in items:
        if item["fcstDate"] != today_str:
            continue
        category = item["category"]
        if category not in ("SKY", "PTY", "POP"):
            continue
        fcst_time = int(item["fcstTime"])
        if start <= fcst_time <= end:
            candidates.setdefault(fcst_time, {})[category] = item["fcstValue"]

    if not candidates:
        return {"sky": "정보없음", "pty": "정보없음", "pop": None}

    def _build(fcst_time: int) -> dict:
        values = candidates[fcst_time]
        return {
            "sky": SKY_MAP.get(values.get("SKY"), "정보없음"),
            "pty": PTY_MAP.get(values.get("PTY"), "정보없음"),
            "pop": int(values["POP"]) if "POP" in values else None,
        }

    # 1순위: 소나기
    for t in sorted(candidates):
        if candidates[t].get("PTY") == "4":
            return _build(t)

    # 2순위: 강수확률 40% 이상인 강수
    for t in sorted(candidates):
        pty = candidates[t].get("PTY")
        pop = candidates[t].get("POP")
        if pty not in (None, "0") and pop is not None and int(pop) >= 40:
            return _build(t)

    # 3순위: 가장 이른 시각
    earliest_time = min(candidates)
    return _build(earliest_time)


def get_today_weather_summary(nx: int, ny: int, now: datetime = None) -> dict:
    """
    오늘 날짜의 예보 데이터를 오전/오후 요약 형태로 가공.
    - 조회 시각(now)의 hour에 따라 4개 구간으로 나눠, 오전/오후 각각
      초단기예보/단기예보/두 소스 병합(merge) 중 무엇을 쓸지 자동 결정 (9-2, 9-3 설계 참고).
    - 오후 시간 범위를 1200~1800에서 1200~2400으로 수정
      (기존에 18~24시가 아예 다뤄지지 않던 문제를 함께 해결).
    - 최저/최고기온은 구간과 무관하게 기존처럼 05시 기준 단기예보로 고정 계산.
    """
    if now is None:
        now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    hour = now.hour

    # ── 최저/최고기온: 기존 방식 그대로 유지 ──
    #tmn_date, tmn_time = _get_base_datetime_for(5, now)
    tmn_date, tmn_time = _get_base_datetime_for(min(hour, 5), now)
    tmn_items = fetch_raw_forecast(nx, ny, tmn_date, tmn_time)

    tmx = None
    for item in tmn_items:
        if item["fcstDate"] == today_str and item["category"] == "TMX":
            tmx = round(float(item["fcstValue"]))

    tmn = None
    tmn_tmp_values = [
        float(item["fcstValue"])
        for item in tmn_items
        if item["fcstDate"] == today_str and item["category"] == "TMP"
    ]
    if tmn_tmp_values:
        tmn = round(min(tmn_tmp_values))

    # ── 구간별 오전/오후 데이터 계산 (9-2 설계) ──
    if hour < 5:
        # 구간1: 자정~05시
        u_date, u_time = _get_ultra_short_base_datetime(now)
        morning_items = fetch_ultra_short_forecast(nx, ny, u_date, u_time)

        s_date, s_time = _get_base_datetime_for(0, now)  # target_hour<5 → 전날 23시
        afternoon_items = fetch_raw_forecast(nx, ny, s_date, s_time)

    elif hour < 12:
        # 구간2: 05시~12시
        u_date, u_time = _get_ultra_short_base_datetime(now)
        morning_items = fetch_ultra_short_forecast(nx, ny, u_date, u_time)

        s_date, s_time = _get_base_datetime_for(hour, now)  # 직전 최근 발표 단기
        afternoon_items = fetch_raw_forecast(nx, ny, s_date, s_time)

    elif hour < 18:
        # 구간3: 12시~18시
        nine_am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        u9_date, u9_time = _get_ultra_short_base_datetime(nine_am)
        morning_items = fetch_ultra_short_forecast(nx, ny, u9_date, u9_time)

        u_date, u_time = _get_ultra_short_base_datetime(now)
        ultra_afternoon_items = fetch_ultra_short_forecast(nx, ny, u_date, u_time)

        s_date, s_time = _get_base_datetime_for(hour, now)
        short_afternoon_items = fetch_raw_forecast(nx, ny, s_date, s_time)

        afternoon_items = _merge_forecast_items(ultra_afternoon_items, short_afternoon_items)

    else:
        # 구간4: 18시~24시
        nine_am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        u9_date, u9_time = _get_ultra_short_base_datetime(nine_am)
        morning_items = fetch_ultra_short_forecast(nx, ny, u9_date, u9_time)

        u_date, u_time = _get_ultra_short_base_datetime(now)
        afternoon_items = fetch_ultra_short_forecast(nx, ny, u_date, u_time)

    morning_summary = _pick_representative(morning_items, today_str, 600, 1200)
    afternoon_summary = _pick_representative(afternoon_items, today_str, 1200, 2400)

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

def _get_ultra_short_base_datetime(now: datetime) -> tuple[str, str]:
    """
    초단기예보 발표시각(매시 30분)을 계산.
    - 발표시각+1시간부터 데이터가 나오는 규칙은 동일하게 적용됨.
    - 예: 지금이 14시 45분이면, 아직 15시 30분 발표분은 안 나왔으므로
      가장 최근인 14시 30분 발표분을 사용.
    - 지금이 14시 20분이면, 14시 30분 발표분도 아직 안 나왔으므로
      그 이전 발표분인 13시 30분을 사용.
    """
    if now.minute >= 30:
        base_dt = now.replace(minute=30, second=0, microsecond=0)
    else:
        base_dt = (now - timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)

    return base_dt.strftime("%Y%m%d"), base_dt.strftime("%H%M")


def fetch_ultra_short_forecast(nx: int, ny: int, base_date: str, base_time: str) -> list[dict]:
    """
    기상청 초단기예보 API를 호출해서 원본 예보 항목(item) 리스트를 그대로 반환.
    - 6시간 이내의 예보만 제공되며, 매시 30분마다 갱신됨.
    - 단기예보(fetch_raw_forecast)와 동일한 구조의 item 리스트를 반환하므로,
      이후 처리 로직(_pick_representative 등)을 그대로 재사용 가능.
    """
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "200",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    response = requests.get(ULTRA_SHORT_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    header = data["response"]["header"]
    if header["resultCode"] != "00":
        raise RuntimeError(f"기상청 초단기예보 API 오류: {header['resultMsg']}")

    return data["response"]["body"]["items"]["item"]


# if __name__ == "__main__":
    # # 초단기예보 단독 테스트
    # now = datetime.now()
    # ultra_date, ultra_time = _get_ultra_short_base_datetime(now)
    # print(f"초단기예보 발표시각: {ultra_date} {ultra_time}")
    # ultra_items = fetch_ultra_short_forecast(nx=61, ny=125, base_date=ultra_date, base_time=ultra_time)
    # print(f"받아온 항목 수: {len(ultra_items)}")
    # print(ultra_items[:5])  # 앞부분 5개만 출력해서 구조 확인

    # #TEST_DATE = datetime(2026, 8, 2)  # 테스트 기준 날짜 (이미 지나간 날짜여야 함)
    # TEST_DATE = datetime.now() - timedelta(days=1)
    # TEST_DATE = TEST_DATE.replace(hour=0, minute=0, second=0, microsecond=0)

    # test_cases = [
    #     ("자정 직전 (23:59)", TEST_DATE.replace(hour=23, minute=59)),
    #     ("자정~05시 이전 (02:30)", TEST_DATE.replace(hour=2, minute=30)),
    #     ("새벽 5시 (05:00)", TEST_DATE.replace(hour=5, minute=0)),
    #     ("경계값 케이스 (17:00, 발표시각+1시간=18시 경계)", TEST_DATE.replace(hour=17, minute=0)),
    #     ("일반 케이스 (14:30)", TEST_DATE.replace(hour=14, minute=30)),
    # ]

    # for label, fake_now in test_cases:
    #     print(f"\n{'=' * 50}")
    #     print(f"[테스트] {label}  (기준 시각: {fake_now})")
    #     print('=' * 50)
    #     try:
    #         summary = get_today_weather_summary(nx=61, ny=126, now=fake_now)
    #         print(summary)
    #         print()
    #         print(format_weather_summary(summary))
    #     except Exception as e:
    #         print(f"에러 발생: {e}")

if __name__ == "__main__":
    now = datetime.now()
    #today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # 오늘(8/5) 새벽이라 아직 당일 데이터가 부족하므로,
    # 확실히 데이터가 존재하는 '어제' 날짜로 고정해서 시간대별 분기 로직만 테스트
    today = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    test_cases = [
        ("구간1: 자정~05시 (02:30)", today.replace(hour=2, minute=30)),
        ("구간2: 05~12시 (09:00)", today.replace(hour=9, minute=0)),
        ("구간2: 05~12시 (11:45)", today.replace(hour=11, minute=45)),
        ("구간3: 12~18시 (13:00)", today.replace(hour=13, minute=0)),
        ("구간3: 12~18시 (17:30)", today.replace(hour=17, minute=30)),
        ("구간4: 18~24시 (19:00)", today.replace(hour=19, minute=0)),
        ("구간4: 18~24시 (23:00)", today.replace(hour=23, minute=0)),
    ]

    for label, fake_now in test_cases:
        print(f"\n{'=' * 50}")
        print(f"[테스트] {label}  (기준 시각: {fake_now})")
        print('=' * 50)
        try:
            summary = get_today_weather_summary(nx=61, ny=125, now=fake_now)
            print(summary)
            print()
            print(format_weather_summary(summary))
        except Exception as e:
            print(f"에러 발생: {e}")    