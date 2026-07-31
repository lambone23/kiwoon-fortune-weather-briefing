"""
사주(만세력) 계산 모듈.
- 실제 계산은 sajupy 라이브러리가 담당.
- sajupy 계산 결과를 sajuinfo.co.kr(외부 만세력 사이트)과 대조 검증함:
  1) 일반 케이스, 2) 자시 경계(23시~01시 출생, 야자시 처리),
  3) 절기 경계 - 입춘 전날, 4) 절기 경계 - 입춘 이후
  총 4가지 케이스 모두 일치 확인됨.
- 기본값(use_solar_time=False)은 위 검증 당시 실제로 사용했던 옵션 없는 상태와
  동일하게 맞춤. 태양시 보정(use_solar_time)은 검증되지 않은 옵션이므로 기본 OFF,
  필요할 때만 명시적으로 켜서 사용 (켤 경우 자시 경계 결과가 달라질 수 있으므로
  재검증 필요).

[고도화 내역]
- 오행 분포에 월지(月支) 기준 왕상휴수사(旺相休囚死) 계절 가중치를 반영해서
  신강/신약 판단 정확도를 높임.
- 십성(十星) 계산 추가 (일간 대비 다른 천간/지지 정기의 오행·음양 관계로 산출,
  정형화된 공식이라 유파차 없이 재현 가능함).
- 대운(大運) 계산 추가: sajupy 패키지에 내장된 절기 정밀 시각 데이터
  (calendar_data.csv)를 이용해 순행/역행 방향과 대운 시작 나이를 정밀 계산.
- 위 고도화 내용은 신한은행 '오늘의 운세' 화면(1990-10-10 14:30 여성 기준)과
  대조 검증함: 십성 7개 항목 전부 일치, 대운 10개 간지(1세~91세) 전부 일치.
- 오늘의 행운 컬러/방향/소재는 신강/신약 판단 + 용신(用神) 개념에 기반한
  결정론적 규칙으로 계산 (LLM이 아닌 코드로 고정 계산).
  ※ 다만 용신 산출 자체는 명리학에서도 유파에 따라 기준이 갈리는 영역이라,
    신한 등 다른 서비스와 완전히 동일한 결과가 나온다고 보장되지는 않음
    (계절 가중치 반영 전보다는 근거가 탄탄해졌으나, "정답"이 하나는 아님).
  ※ 계절 가중치는 월지 그룹(인묘진/사오미/신유술/해자축)만으로 단순화했고,
    진술축미(辰戌丑未)의 토왕(土旺) 세부 보정이나 통근(通根)/조후(調候)는
    반영하지 않음 (TODO: 추후 고도화 여지).
- 대운 계산은 sajupy 패키지 내부에 포함된 calendar_data.csv 파일 경로에
  의존함 (공식 공개 API는 아니라 패키지 버전업 시 경로가 바뀌면 깨질 수 있음,
  TODO: 추후 별도 절기 데이터 소스로 교체 검토).
"""

import os
from datetime import datetime

import pandas as pd
import sajupy
from sajupy import calculate_saju, lunar_to_solar


def get_saju(year: int, month: int, day: int, hour: int, minute: int = 0,
             use_solar_time: bool = False, city: str = None, utc_offset: int = 9) -> dict:
    """
    생년월일시를 입력받아 사주(년/월/일/시주) 정보를 계산해서 반환.

    기본값(use_solar_time=False)은 1-11에서 sajuinfo.co.kr과 대조 검증한
    상태와 동일함. 태양시 보정을 쓰고 싶으면 use_solar_time=True와 city를
    명시적으로 넘겨야 함 (단, 자시/야자시 경계에서 결과가 달라질 수 있으므로
    별도 검증 필요).
    """
    kwargs = dict(year=year, month=month, day=day, hour=hour, minute=minute)
    if use_solar_time:
        kwargs.update(city=city, use_solar_time=True, utc_offset=utc_offset)
    return calculate_saju(**kwargs)

def get_saju_from_lunar(lunar_year: int, lunar_month: int, lunar_day: int, hour: int,
                          minute: int = 0, is_leap_month: bool = False, **kwargs) -> dict:
    """
    음력 생년월일시를 받아 양력으로 변환한 뒤 사주를 계산.
    """
    converted = lunar_to_solar(lunar_year, lunar_month, lunar_day, is_leap_month)
    return get_saju(converted["solar_year"], converted["solar_month"], converted["solar_day"],
                     hour, minute, **kwargs)

def format_saju_summary(saju: dict) -> str:
    """
    사주 계산 결과를 LLM 프롬프트에 넣기 좋은 텍스트로 정리.
    """
    return (
        f"년주: {saju['year_pillar']} ({saju['year_stem']}{saju['year_branch']})\n"
        f"월주: {saju['month_pillar']} ({saju['month_stem']}{saju['month_branch']})\n"
        f"일주: {saju['day_pillar']} ({saju['day_stem']}{saju['day_branch']})\n"
        f"시주: {saju['hour_pillar']} ({saju['hour_stem']}{saju['hour_branch']})"
    )


# ── 오행(五行) 기본 데이터 ──────────────────────────────────────

# 천간(天干) 10개를 오행으로 분류
STEM_TO_ELEMENT = {
    "甲": "목", "乙": "목",
    "丙": "화", "丁": "화",
    "戊": "토", "己": "토",
    "庚": "금", "辛": "금",
    "壬": "수", "癸": "수",
}

# 천간 10개의 음양
STEM_YINYANG = {
    "甲": "양", "乙": "음",
    "丙": "양", "丁": "음",
    "戊": "양", "己": "음",
    "庚": "양", "辛": "음",
    "壬": "양", "癸": "음",
}

# 지장간(支藏干): 지지 안에 숨어있는 천간들.
# (여기/중기, 정기) 순서, 가중치는 여기·중기 0.3, 정기 1.0으로 단순화.
# ※ 실제 지장간 일수 비중은 지지마다 다르고 유파별 차이도 있으나,
#   여기서는 "정기의 영향이 가장 크다"는 원칙만 반영한 단순화된 가중치.
HIDDEN_STEMS = {
    "子": [("癸", 1.0)],
    "丑": [("癸", 0.3), ("辛", 0.3), ("己", 1.0)],
    "寅": [("戊", 0.3), ("丙", 0.3), ("甲", 1.0)],
    "卯": [("乙", 1.0)],
    "辰": [("乙", 0.3), ("癸", 0.3), ("戊", 1.0)],
    "巳": [("戊", 0.3), ("庚", 0.3), ("丙", 1.0)],
    "午": [("丙", 0.3), ("己", 0.3), ("丁", 1.0)],
    "未": [("丁", 0.3), ("乙", 0.3), ("己", 1.0)],
    "申": [("戊", 0.3), ("壬", 0.3), ("庚", 1.0)],
    "酉": [("辛", 1.0)],
    "戌": [("辛", 0.3), ("丁", 0.3), ("戊", 1.0)],
    "亥": [("戊", 0.3), ("甲", 0.3), ("壬", 1.0)],
}

# 오행 상생(相生): 이 오행이 生하는(만들어주는) 오행 = 순방향 생성 관계
GENERATES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
# 오행 상생 역방향: 이 오행을 生해주는(도와주는) 오행 = 인성(印星)
GENERATED_BY = {v: k for k, v in GENERATES.items()}

# 오행 상극(相剋): 이 오행이 剋하는(억누르는) 오행 = 순방향 극 관계
CONTROLS = {"목": "토", "화": "금", "토": "수", "금": "목", "수": "화"}
# 오행 상극 역방향: 이 오행을 剋하는(억누르는) 오행 = 관성(官星)
CONTROLLED_BY = {v: k for k, v in CONTROLS.items()}

# 월지(月支) 그룹별 계절 오행 (왕상휴수사 판단 기준)
# ※ 진술축미(辰戌丑未)의 토왕(土旺) 세부 보정은 반영하지 않은 단순화 버전.
SEASON_BY_BRANCH = {
    "寅": "목", "卯": "목", "辰": "목",   # 봄 - 목 왕성
    "巳": "화", "午": "화", "未": "화",   # 여름 - 화 왕성
    "申": "금", "酉": "금", "戌": "금",   # 가을 - 금 왕성
    "亥": "수", "子": "수", "丑": "수",   # 겨울 - 수 왕성
}

# 왕상휴수사(旺相休囚死) 상태별 가중치
WANGSANGHYUSUSA_WEIGHT = {
    "왕": 1.0,  # 계절과 같은 오행 - 가장 왕성
    "상": 0.8,  # 계절 오행이 생하는 오행 - 다음으로 왕성
    "휴": 0.5,  # 계절 오행을 생하는 오행(부모, 쉬는 상태)
    "수": 0.3,  # 계절 오행이 극하는 오행 - 갇힌 상태
    "사": 0.2,  # 계절 오행을 극하는 오행 - 가장 쇠약
}

# 오행별 행운 컬러 / 방향 / 소재
ELEMENT_LUCKY_INFO = {
    "목": {"color": "초록·청록 계열", "direction": "동쪽", "material": "나무 재질"},
    "화": {"color": "빨강·주황 계열", "direction": "남쪽", "material": "가죽 또는 붉은 보석"},
    "토": {"color": "노랑·베이지 계열", "direction": "중앙", "material": "도자기 또는 흙 소재"},
    "금": {"color": "흰색·은색 계열", "direction": "서쪽", "material": "금속 소재"},
    "수": {"color": "파랑·검정 계열", "direction": "북쪽", "material": "유리 또는 수정 소재"},
}


def get_element_distribution(saju: dict) -> dict:
    """
    사주 여덟 글자(천간 4개 + 지지 4개, 지지 속 지장간 포함)를 오행별로
    집계한 '기본' 분포 점수 (계절 가중치 반영 전).

    Returns:
        dict: {"목": 0.3, "화": 2.9, "토": 4.6, "금": 2.3, "수": 0.3} 형태
    """
    counts = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}

    stems = [saju["year_stem"], saju["month_stem"], saju["day_stem"], saju["hour_stem"]]
    branches = [saju["year_branch"], saju["month_branch"], saju["day_branch"], saju["hour_branch"]]

    for stem in stems:
        counts[STEM_TO_ELEMENT[stem]] += 1.0

    for branch in branches:
        for hidden_stem, weight in HIDDEN_STEMS[branch]:
            counts[STEM_TO_ELEMENT[hidden_stem]] += weight

    return counts


def get_wangsanghyususa_map(season_element: str) -> dict:
    """
    주어진 계절 오행을 기준으로, 오행 5개 각각이 왕/상/휴/수/사 중
    어느 상태에 해당하는지 매핑해서 반환.
    """
    return {
        season_element: "왕",
        GENERATES[season_element]: "상",
        GENERATED_BY[season_element]: "휴",
        CONTROLS[season_element]: "수",
        CONTROLLED_BY[season_element]: "사",
    }


def get_weighted_element_distribution(saju: dict) -> dict:
    """
    기본 오행 분포에 월지(계절) 기준 왕상휴수사 가중치를 곱해서
    계절 영향을 반영한 오행 분포를 계산.
    """
    base = get_element_distribution(saju)
    season = SEASON_BY_BRANCH[saju["month_branch"]]
    state_map = get_wangsanghyususa_map(season)
    return {element: value * WANGSANGHYUSUSA_WEIGHT[state_map[element]]
            for element, value in base.items()}


def get_day_master_strength(saju: dict) -> str:
    """
    일간의 신강/신약을 판단.
    - 계절 가중치가 반영된 오행 분포를 기준으로, 일간과 같은 오행(비겁) +
      일간을 생조하는 오행(인성)의 합이 전체의 절반 이상이면 신강,
      그렇지 않으면 신약으로 판단.
    - 참고: 실제로는 통근(通根) 여부, 조후(調候) 등이 함께 고려되는 경우가
      많으나, 여기서는 계절 가중 오행 분포 비중만으로 판단 (TODO: 고도화 여지).
    """
    weighted = get_weighted_element_distribution(saju)
    total = sum(weighted.values())

    user_element = STEM_TO_ELEMENT[saju["day_stem"]]
    supporting_element = GENERATED_BY[user_element]  # 인성

    support_score = weighted[user_element] + weighted[supporting_element]

    return "신강" if support_score >= total / 2 else "신약"


def get_yongsin_element(saju: dict) -> str:
    """
    신강/신약 판단에 따라 용신(오늘의 행운 오행)이 되는 오행을 결정.
    - 신강: 일간을 극하는 오행(관성)을 용신으로 사용 — 넘치는 기운을 눌러줌
    - 신약: 일간을 생조하는 오행(인성)을 용신으로 사용 — 부족한 기운을 도와줌
    """
    user_element = STEM_TO_ELEMENT[saju["day_stem"]]
    strength = get_day_master_strength(saju)

    if strength == "신강":
        return CONTROLLED_BY[user_element]
    else:
        return GENERATED_BY[user_element]


def get_lucky_info(saju: dict) -> dict:
    """
    사용자의 전체 사주 정보를 바탕으로 신강/신약 판단 및 용신을 계산하고,
    그에 맞는 오늘의 행운 컬러/방향/소재 정보를 반환.

    Args:
        saju: get_saju()가 반환한 사주 딕셔너리 전체

    Returns:
        dict: {"element": "목", "color": "초록·청록 계열", "direction": "동쪽",
               "material": "나무 재질"}
    """
    lucky_element = get_yongsin_element(saju)
    info = ELEMENT_LUCKY_INFO[lucky_element]
    return {"element": lucky_element, **info}


def format_lucky_info(lucky: dict) -> str:
    """
    get_lucky_info() 결과를 LLM 프롬프트에 넣기 좋은 텍스트로 정리.
    """
    return (
        f"행운 오행: {lucky['element']}\n"
        f"행운 컬러: {lucky['color']}\n"
        f"행운 방향: {lucky['direction']}\n"
        f"행운 소재: {lucky['material']}"
    )


# ── 십성(十星) 계산 ──────────────────────────────────────

def get_ten_god(day_stem: str, target_stem: str) -> str:
    """
    일간(day_stem) 대비 다른 천간(target_stem)의 십성 관계를 계산.
    표준 십성 공식(오행 생/극 관계 + 음양 일치 여부)을 그대로 적용한
    정형화된 계산이라, 유파차 없이 재현 가능함.

    - 같은 오행, 같은 음양: 비견
    - 같은 오행, 다른 음양: 겁재
    - 일간이 생하는 오행, 같은 음양: 식신
    - 일간이 생하는 오행, 다른 음양: 상관
    - 일간이 극하는 오행, 같은 음양: 편재
    - 일간이 극하는 오행, 다른 음양: 정재
    - 일간을 극하는 오행, 같은 음양: 편관
    - 일간을 극하는 오행, 다른 음양: 정관
    - 일간을 생하는 오행, 같은 음양: 편인
    - 일간을 생하는 오행, 다른 음양: 정인(인수)
    """
    day_element, day_yinyang = STEM_TO_ELEMENT[day_stem], STEM_YINYANG[day_stem]
    target_element, target_yinyang = STEM_TO_ELEMENT[target_stem], STEM_YINYANG[target_stem]
    same_polarity = (day_yinyang == target_yinyang)

    if target_element == day_element:
        return "비견" if same_polarity else "겁재"
    if GENERATES[day_element] == target_element:
        return "식신" if same_polarity else "상관"
    if CONTROLS[day_element] == target_element:
        return "편재" if same_polarity else "정재"
    if CONTROLS[target_element] == day_element:
        return "편관" if same_polarity else "정관"
    if GENERATES[target_element] == day_element:
        return "편인" if same_polarity else "정인"

    raise ValueError(f"십성 매칭 실패: day_stem={day_stem}, target_stem={target_stem}")


def get_ten_gods_summary(saju: dict) -> dict:
    """
    사주 전체(일간을 제외한 년/월/시간 천간 + 년/월/일/시지)에 대해
    십성을 계산해서 반환.
    - 지지의 십성은 해당 지지의 지장간 중 정기(주된 기운)를 기준으로 계산
      (일반적인 만세력 서비스들의 표기 방식과 동일).
    """
    day_stem = saju["day_stem"]
    result = {}

    for label, stem in [("년간", saju["year_stem"]),
                         ("월간", saju["month_stem"]),
                         ("시간", saju["hour_stem"])]:
        result[label] = get_ten_god(day_stem, stem)

    for label, branch in [("년지", saju["year_branch"]),
                           ("월지", saju["month_branch"]),
                           ("일지", saju["day_branch"]),
                           ("시지", saju["hour_branch"])]:
        main_qi_stem = HIDDEN_STEMS[branch][-1][0]  # 지장간 중 정기(마지막 항목)
        result[label] = get_ten_god(day_stem, main_qi_stem)

    return result


def format_ten_gods_summary(ten_gods: dict) -> str:
    """
    get_ten_gods_summary() 결과를 텍스트로 정리.
    """
    return "\n".join(f"{key}: {value}" for key, value in ten_gods.items())


# ── 대운(大運) 계산 ──────────────────────────────────────

STEMS_ORDER = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
BRANCHES_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 대운 계산 기준이 되는 12개 "절(節)" 이름 (월이 바뀌는 절기만 해당,
# "중기" 절기는 대운 계산에 사용하지 않음)
JEOL_NAMES = ['입춘', '경칩', '청명', '입하', '망종', '소서',
              '입추', '백로', '한로', '입동', '대설', '소한']

# sajupy 패키지에 내장된 절기 정밀 시각 데이터 경로
# ※ 공식 공개 API가 아니라 패키지 내부 파일 구조에 의존함.
#   sajupy 버전업 시 이 파일 경로/형식이 바뀌면 아래 함수가 깨질 수 있음.
_CSV_PATH = os.path.join(os.path.dirname(sajupy.__file__), 'calendar_data.csv')
_JEOL_TABLE_CACHE = None


def _load_jeol_table() -> pd.DataFrame:
    """
    sajupy 내장 데이터에서 12개 '절' 절기의 정밀 시각(연/월/일/시/분)을
    불러와서 정렬된 표로 반환. 최초 호출 시 한 번만 로드하고 캐싱함.
    """
    global _JEOL_TABLE_CACHE
    if _JEOL_TABLE_CACHE is not None:
        return _JEOL_TABLE_CACHE

    df = pd.read_csv(_CSV_PATH)
    jeol = df[df['solar_term_korean'].isin(JEOL_NAMES)].copy()
    jeol['term_time'] = jeol['term_time'].astype('Int64').astype(str)
    jeol['dt'] = pd.to_datetime(jeol['term_time'], format='%Y%m%d%H%M', errors='coerce')
    jeol = jeol.dropna(subset=['dt']).sort_values('dt').reset_index(drop=True)

    _JEOL_TABLE_CACHE = jeol
    return jeol


def step_ganzhi(stem: str, branch: str, step: int) -> str:
    """
    60갑자 순환에서 주어진 간지를 step만큼(순행 +1 / 역행 -1) 이동한
    다음 간지를 반환. 천간(10주기)과 지지(12주기)를 각각 독립적으로
    같은 step만큼 이동시키는 방식 (60갑자 순환의 표준 계산법).
    """
    stem_idx = (STEMS_ORDER.index(stem) + step) % 10
    branch_idx = (BRANCHES_ORDER.index(branch) + step) % 12
    return STEMS_ORDER[stem_idx] + BRANCHES_ORDER[branch_idx]


def get_daeun(saju: dict, year: int, month: int, day: int, hour: int, minute: int,
              gender: str, periods: int = 9) -> dict:
    """
    대운(大運)을 계산. 10년 단위로 바뀌는 인생의 큰 운세 흐름을 나타냄.

    - 방향(순행/역행): 년간의 음양 + 성별로 결정
      (양간+남성 또는 음간+여성 → 순행 / 양간+여성 또는 음간+남성 → 역행)
    - 시작 나이: 생일로부터 다음(순행) 또는 이전(역행) '절(節)' 절기까지의
      정밀 일수를 계산해서, 3일 = 1년 기준으로 환산 (전통 명리학 공식).
    - 대운 시작 간지: 월주를 기준으로, 방향에 따라 60갑자를 한 칸씩
      이동하며 10년 단위로 나열.

    Args:
        saju: get_saju() 결과 (사주 딕셔너리 전체)
        year, month, day, hour, minute: 생년월일시 (get_saju()에 넣은 값과 동일해야 함)
        gender: "남성" 또는 "여성" (대운 방향 결정에 반드시 필요)
        periods: 계산할 대운 개수 (기본 9개, 약 90년치)

    Returns:
        dict: {"direction": "역행", "start_age": 1,
               "periods": [{"age_from": 1, "ganzhi": "乙酉"}, ...]}
    """
    if gender not in ("남성", "여성"):
        raise ValueError("gender는 '남성' 또는 '여성'이어야 합니다 (대운 순행/역행 방향 결정에 필수).")

    birth_dt = datetime(year, month, day, hour, minute)
    jeol_table = _load_jeol_table()

    is_yang_year = (STEM_YINYANG[saju["year_stem"]] == "양")
    is_male = (gender == "남성")
    forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
    step = 1 if forward else -1

    if forward:
        candidates = jeol_table[jeol_table['dt'] > birth_dt]
        if len(candidates) == 0:
            raise ValueError("이후 절기 데이터를 찾을 수 없습니다 (지원 범위 밖 날짜일 수 있음).")
        nearest = candidates.iloc[0]
        delta_days = (nearest['dt'] - birth_dt).total_seconds() / 86400
    else:
        candidates = jeol_table[jeol_table['dt'] <= birth_dt]
        if len(candidates) == 0:
            raise ValueError("이전 절기 데이터를 찾을 수 없습니다 (지원 범위 밖 날짜일 수 있음).")
        nearest = candidates.iloc[-1]
        delta_days = (birth_dt - nearest['dt']).total_seconds() / 86400

    start_age = round(delta_days / 3)
    if start_age == 0:
        start_age = 1  # 관례상 0세 표기 대신 1세부터 표기

    stem, branch = saju["month_stem"], saju["month_branch"]
    result_periods = []
    for i in range(periods):
        gz = step_ganzhi(stem, branch, step)
        stem, branch = gz[0], gz[1]
        result_periods.append({"age_from": start_age + i * 10, "ganzhi": gz})

    return {
        "direction": "순행" if forward else "역행",
        "start_age": start_age,
        "periods": result_periods,
    }


def format_daeun_summary(daeun: dict) -> str:
    """
    get_daeun() 결과를 텍스트로 정리.
    """
    lines = [f"대운 방향: {daeun['direction']} (시작 나이: {daeun['start_age']}세)"]
    for period in daeun["periods"]:
        lines.append(f"{period['age_from']}세~: {period['ganzhi']}")
    return "\n".join(lines)


if __name__ == "__main__":
    saju = get_saju(1990, 10, 10, 14, 30)
    print(saju)
    print()
    print(format_saju_summary(saju))
    print()

    weighted = get_weighted_element_distribution(saju)
    print(f"계절 가중 오행 분포: { {k: round(v, 2) for k, v in weighted.items()} }")
    print(f"신강/신약: {get_day_master_strength(saju)}")
    print()

    lucky = get_lucky_info(saju)
    print(format_lucky_info(lucky))
    print()

    ten_gods = get_ten_gods_summary(saju)
    print("[십성]")
    print(format_ten_gods_summary(ten_gods))
    print()

    daeun = get_daeun(saju, 1990, 10, 10, 14, 30, gender="여성", periods=10)
    print("[대운]")
    print(format_daeun_summary(daeun))