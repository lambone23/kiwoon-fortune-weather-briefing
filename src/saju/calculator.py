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

[고도화 내역 - 1차]
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
- 대운 계산은 sajupy 패키지 내부에 포함된 calendar_data.csv 파일 경로에
  의존함 (공식 공개 API는 아니라 패키지 버전업 시 경로가 바뀌면 깨질 수 있음).

[고도화 내역 - 2차: 신강/신약·용신 계산 로직 전면 재검토]
- 지장간 가중치를 지지 균일값에서, 월률분야(月律分野) 일수표 기준
  "일수/30" 계산식으로 세분화 (반올림 오차 없음).
- 왕상휴수사 가중치 수치는 유지, 다섯 관계(왕/상/휴/수/사)의 방향 설명을
  코드 주석에 명확히 재정리.
- 신강/신약 판단에 통근(通根: 일간과 지장간의 천간 일치 여부)과 월령(月令:
  월지 정기 자리의 중요도) 보정을 추가 반영.
- 진술축미(辰戌丑未) 토왕(土旺) 보정 추가: 계절 분류는 유지하되, 해당
  지지에서 "토"의 왕상휴수사 상태를 한 단계 완화.
- 신강/신약 판정 로직을 "지원 세력(비겁+인성) >= 소모 세력(식상+재성+관성)"
  비교로 명시적으로 재구성 (계산 결과는 기존과 동일, 확장성 개선).
- 대운 시작 나이 계산을 round()에서 floor()(절사)로 변경 — 경계값 테스트
  (1990-02-05, raw=9.5387)에서 round=10, floor=9로 실제 차이 확인됨.
  신한 대조 케이스(1990-10-10)는 두 방식이 우연히 일치해(둘 다 9세)
  기존 검증에는 영향 없음.
- 절기 데이터 파일(calendar_data.csv) 로드 시 존재 여부를 먼저 확인하여,
  파일을 찾지 못할 경우 원인과 해결 방법을 안내하는 에러 메시지 추가.
- 용신 계산(get_yongsin_element)은 로직 변경 없이, "억부법 기준 용신
  후보"임을 명확히 하는 문서화만 보강.

※ 아래 항목은 이번 2차 고도화에서도 여전히 미반영 (TODO, 향후 검토 대상):
  - 투간(透干): 월지 정기가 천간에도 같은 글자로 드러나는지
  - 조후(調候): 계절의 한난조습에 따른 별도 보정
  - 격국(格局): 신강/신약과는 별개의 분석 축
  - 통관(通關) / 병약(病藥) 관점의 용신 검토
  - 辰(습토)/未(조토)/戌(건토)/丑(한습토) 각각의 성격 차이 (현재는
    넷을 동일하게 "토왕"으로만 취급하는 단순화 모델)
  이들은 전체 명식 해석·격국·조후·희기판단 등 선행 체계가 필요한
  영역이라, 단순 함수 추가 수준을 넘어서는 별도 고도화 작업으로 남김.
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

    기본값(use_solar_time=False)은 1-11에서 sajuinfo.co.kr과 대조 검증한 상태와 동일함.
    태양시 보정을 쓰고 싶으면 use_solar_time=True와 city를 명시적으로 넘겨야 함
    (단, 자시/야자시 경계에서 결과가 달라질 수 있으므로 별도 검증 필요).
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
# (여기/중기, 정기) 순서. 가중치는 월률분야(月律分野) 일수표를 기준으로
# "일수 / 30"을 계산식 그대로 사용 (반올림 오차 없이, 문헌의 일수와
# 코드가 1:1로 대응되도록 함).
# ※ 이 일수 자체는 명리학 문헌 중 가장 널리 인용되는 버전을 채택한 것으로,
#   유파에 따라 세부 일수가 1~2일씩 다르게 제시되기도 함 (절대 정답 아님,
#   기존 균일 가중치보다 근거가 명확한 근사치로 개선한 것).
HIDDEN_STEMS = {
    "子": [("癸", 30 / 30)],
    "丑": [("癸", 9 / 30), ("辛", 3 / 30), ("己", 18 / 30)],
    "寅": [("戊", 7 / 30), ("丙", 7 / 30), ("甲", 16 / 30)],
    "卯": [("乙", 30 / 30)],
    "辰": [("乙", 9 / 30), ("癸", 3 / 30), ("戊", 18 / 30)],
    "巳": [("戊", 7 / 30), ("庚", 7 / 30), ("丙", 16 / 30)],
    "午": [("丙", 10 / 30), ("己", 9 / 30), ("丁", 11 / 30)],
    "未": [("丁", 9 / 30), ("乙", 3 / 30), ("己", 18 / 30)],
    "申": [("戊", 7 / 30), ("壬", 7 / 30), ("庚", 16 / 30)],
    "酉": [("辛", 30 / 30)],
    "戌": [("辛", 9 / 30), ("丁", 3 / 30), ("戊", 18 / 30)],
    "亥": [("戊", 7 / 30), ("甲", 7 / 30), ("壬", 16 / 30)],
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
# ※ 진술축미(辰戌丑未)는 이 표에서는 각자 원래 계절(봄/여름/가을/겨울)
#   오행으로 분류되어 있고, 토왕(土旺) 보정은 별도로 TOWANG_BRANCHES와
#   get_wangsanghyususa_map()에서 처리함 (아래 참고).
SEASON_BY_BRANCH = {
    "寅": "목", "卯": "목", "辰": "목",   # 봄 - 목 왕성
    "巳": "화", "午": "화", "未": "화",   # 여름 - 화 왕성
    "申": "금", "酉": "금", "戌": "금",   # 가을 - 금 왕성
    "亥": "수", "子": "수", "丑": "수",   # 겨울 - 수 왕성
}

# 왕상휴수사(旺相休囚死) 상태별 가중치
# ※ 왕상휴수사의 순서(왕>상>휴>수>사)는 명리학 정통 이론이나, 이를 구체적
#   숫자 비율로 정량화한 표준 공식은 명리학 문헌에 존재하지 않음. 아래
#   수치는 순서와 방향성만 반영한 근사치이며, "정답 숫자"가 아님을 명시함.
#   (TODO: 통근·투간 등을 함께 고려하는 방식으로 대체 검토)
#
# 각 상태의 정확한 관계 (get_wangsanghyususa_map() 로직 기준):
#   왕(旺): 계절을 얻은 오행 (계절 오행 자신)
#   상(相): 왕한 오행이 생해주는 오행
#   휴(休): 왕한 오행을 생해준 오행 (부모뻘 오행)
#   수(囚): 왕한 오행에게 극을 받는 오행
#   사(死): 왕한 오행을 극하는 오행
WANGSANGHYUSUSA_WEIGHT = {
    "왕": 1.0,  # 계절을 얻은 오행 - 가장 왕성
    "상": 0.8,  # 왕한 오행이 생해주는 오행 - 다음으로 왕성
    "휴": 0.5,  # 왕한 오행을 생해준 오행 (부모뻘) - 쉬는 상태
    "수": 0.3,  # 왕한 오행에게 극을 받는 오행 - 갇힌 상태
    "사": 0.2,  # 왕한 오행을 극하는 오행 - 가장 쇠약
}

# 오행별 행운 컬러 / 방향 / 소재
ELEMENT_LUCKY_INFO = {
    "목": {"color": "초록·청록 계열", "direction": "동쪽", "material": "나무 재질"},
    "화": {"color": "빨강·주황 계열", "direction": "남쪽", "material": "가죽 또는 붉은 보석"},
    "토": {"color": "노랑·베이지 계열", "direction": "중앙", "material": "도자기 또는 흙 소재"},
    "금": {"color": "흰색·은색 계열", "direction": "서쪽", "material": "금속 소재"},
    "수": {"color": "파랑·검정 계열", "direction": "북쪽", "material": "유리 또는 수정 소재"},
}


# ── 신강/신약 판단 보정 (2차 고도화) ──────────────────────────────

# 통근(通根) 가중치: 일간과 같은 오행이 지지의 지장간에 존재할 때
# (=뿌리를 내렸을 때) 해당 지장간의 기여도에 곱하는 보너스 배율.
# - 같은 천간(예: 일간 甲, 지장간 甲): 강한 통근
# - 같은 오행, 다른 천간(예: 일간 甲, 지장간 乙): 약한 통근
# ※ 통근의 "있다/없다" 개념 자체는 명리학 정통 이론이나, 이를 정량화한
#   표준 배율은 문헌에 존재하지 않음. 아래 값은 방향성만 반영한 근사치.
TONGGEUN_BONUS_STRONG = 1.5  # 같은 천간
TONGGEUN_BONUS_WEAK = 1.2    # 같은 오행, 다른 천간

# 월령(月令) 보너스: 월지가 "그 계절의 주도권을 쥔 자리"라는 명리 개념을
# 반영하기 위한 추가 가중치. 왕상휴수사(계절에 따른 오행 강약)와는 별개로,
# "월지라는 자리 자체"의 중요도를 한 번 더 반영함.
# ※ 오직 월지의 지장간 "정기"(그 지지를 대표하는 주된 기운) 항목에만 적용.
#   천간(년간/월간/일간/시간)에는 적용하지 않음 — 월령은 지지 개념이므로.
# ※ 1.3은 정량화된 표준값이 아니라 구현상 근사치.
MONTH_BRANCH_BONUS = 1.3

# 진술축미(辰戌丑未) 토왕 지지: 봄/여름/가을/겨울 각 계절의 끝자락에
# 위치하며, 다음 계절로 전환되는 시기에 土 기운이 함께 강해진다는
# 명리학 개념(토왕, 土旺)이 적용되는 지지.
# ※ 토왕 보정은 진술축미가 "토의 계절"이라는 의미가 아니라, 각 계절
#   전환기의 토 기운 개입을 반영하는 보정이다. 기존 계절 분류
#   (辰=목, 戌=금 등)는 그대로 유지하고, 이 지지들에 한해 "土"의
#   왕상휴수사 상태만 한 단계 완화하는 방식으로 반영한다.
#   (완전히 "토 계절"로 재분류하지 않는 이유: 그렇게 하면 원래 계절
#   오행 — 예: 戌月의 金 — 의 계절적 주도권이 사라지는 과도한
#   변경이 되므로)
# ※ 辰(습토)/未(조토)/戌(건토)/丑(한습토) 각각의 성격 차이는 현재
#   미반영 — 넷을 동일하게 취급하는 단순화 모델. 향후 조후·지장간
#   심화 모델에서 확장 가능.
# ※ 여러 보정(지장간·통근·월령·토왕)이 같은 오행에 동시에 적용될 수
#   있으나, 이는 반복 강화 오류가 아니라 각각 존재량·뿌리·자리·계절
#   성격이라는 서로 다른 관점을 누적 반영하는 다중 보정이다. 다만
#   여러 보정이 동일 오행에 집중되어 결과가 과도하게 강하게 나타나는
#   경우가 확인되면, 구조 자체보다 개별 배율을 우선 조정한다.
#   조정 우선순위: 1순위 MONTH_BRANCH_BONUS, 2순위
#   TONGGEUN_BONUS_STRONG, 3순위 토왕 완화 단계.
TOWANG_BRANCHES = {"辰", "戌", "丑", "未"}

# 왕상휴수사 상태의 순서 (완화 시 한 단계씩 좋은 쪽으로 이동)
WANGSANGHYUSUSA_ORDER = ["사", "수", "휴", "상", "왕"]


def get_element_distribution(saju: dict) -> dict:
    """
    사주 여덟 글자(천간 4개 + 지지 4개, 지지 속 지장간 포함)를 오행별로
    집계한 '기본' 분포 점수 (계절 가중치 반영 전).

    아래 두 가지 보정을 지장간 개별 항목 단계(오행으로 합산되기 전)에서
    함께 반영함:
    - 통근(通根): 일간과 같은 오행/천간이 지지에 뿌리를 두고 있는지
    - 월령(月令): 월지의 정기가 그 계절의 주도권을 쥔 자리인지
    두 보정 모두 "지지"에만 적용되며, 천간 4개(년간/월간/일간/시간)에는
    적용하지 않음.

    ※ 미반영 요소 (TODO, 향후 고도화 영역):
    - 투간(透干): 월지 정기가 천간에도 같은 글자로 드러나는지
    - 조후(調候): 계절의 한난조습에 따른 별도 보정
    - 격국(格局): 신강/신약과는 별개의 분석 축 (이 함수의 목표 범위 밖)

    Returns:
        dict: {"목": 0.3, "화": 2.9, "토": 4.6, "금": 2.3, "수": 0.3} 형태
    """
    counts = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}
    day_stem = saju["day_stem"]
    day_element = STEM_TO_ELEMENT[day_stem]
    month_branch = saju["month_branch"]

    stems = [saju["year_stem"], saju["month_stem"], saju["day_stem"], saju["hour_stem"]]
    branches = [saju["year_branch"], saju["month_branch"], saju["day_branch"], saju["hour_branch"]]

    # 천간: 통근/월령 보정 대상 아님, 기본 1.0 그대로
    for stem in stems:
        counts[STEM_TO_ELEMENT[stem]] += 1.0

    # 지지(지장간): 통근 + 월령 보정을 개별 항목 단계에서 함께 적용
    for branch in branches:
        hidden_stem_list = HIDDEN_STEMS[branch]
        last_index = len(hidden_stem_list) - 1

        for index, (hidden_stem, weight) in enumerate(hidden_stem_list):
            contribution = weight
            hidden_element = STEM_TO_ELEMENT[hidden_stem]

            # ① 통근 보정
            if hidden_stem == day_stem:
                contribution *= TONGGEUN_BONUS_STRONG
            elif hidden_element == day_element:
                contribution *= TONGGEUN_BONUS_WEAK

            # ② 월령 보정: 월지의 "정기"(마지막 항목)에만 적용
            if branch == month_branch and index == last_index:
                contribution *= MONTH_BRANCH_BONUS

            counts[hidden_element] += contribution

    return counts


def get_wangsanghyususa_map(season_element: str, month_branch: str = None) -> dict:
    """
    주어진 계절 오행을 기준으로, 오행 5개 각각이 왕/상/휴/수/사 중
    어느 상태에 해당하는지 매핑해서 반환.

    month_branch가 진술축미(TOWANG_BRANCHES)에 해당하면, "토"의 상태를
    한 단계 완화(사→수, 수→휴, 휴→상 등)해서 토왕 개념을 반영함.
    이 함수를 호출하는 다른 위치가 있다면, month_branch를 반드시
    함께 넘겨야 토왕 보정이 정상 반영됨 (넘기지 않으면 기존과
    동일하게 토왕 보정 없이 동작).
    """
    base_map = {
        season_element: "왕",
        GENERATES[season_element]: "상",
        GENERATED_BY[season_element]: "휴",
        CONTROLS[season_element]: "수",
        CONTROLLED_BY[season_element]: "사",
    }

    if month_branch in TOWANG_BRANCHES and base_map.get("토") != "왕":
        current_state = base_map["토"]
        current_index = WANGSANGHYUSUSA_ORDER.index(current_state)
        upgraded_state = WANGSANGHYUSUSA_ORDER[min(current_index + 1, len(WANGSANGHYUSUSA_ORDER) - 1)]
        base_map["토"] = upgraded_state

    return base_map


def get_weighted_element_distribution(saju: dict) -> dict:
    """
    get_element_distribution()(천간+지장간+통근+월령 반영 완료)에
    월지(계절) 기준 왕상휴수사 가중치만 순수하게 곱해서 반환.
    - 월지가 진술축미(辰戌丑未)에 해당하면 토왕 보정도 함께 반영됨
      (get_wangsanghyususa_map() 내부에서 처리).
    """
    base = get_element_distribution(saju)
    month_branch = saju["month_branch"]
    season = SEASON_BY_BRANCH[month_branch]
    state_map = get_wangsanghyususa_map(season, month_branch)
    return {element: value * WANGSANGHYUSUSA_WEIGHT[state_map[element]]
            for element, value in base.items()}


def get_day_master_strength(saju: dict) -> str:
    """
    일간의 신강/신약을 판단.
    - 지원 세력(비겁+인성)과 소모 세력(식상+재성+관성)을 각 오행을
      명시적으로 짚어서 비교. (수학적으로는 기존의 "지원 세력 >= 전체
      절반"과 동일한 결과를 내지만, 코드가 명리학 개념과 직접 대응하도록
      표현을 개선함 — 향후 세력별 추가 보정을 넣기 쉬운 구조)

    ※ 미반영 요소 (TODO, 향후 고도화 영역):
    - 투간, 조후, 격국은 반영하지 않음 (get_element_distribution() 참고)
    """
    weighted = get_weighted_element_distribution(saju)

    user_element = STEM_TO_ELEMENT[saju["day_stem"]]
    supporting_element = GENERATED_BY[user_element]     # 인성
    output_element = GENERATES[user_element]            # 식상 (내가 생하는 오행)
    wealth_element = CONTROLS[user_element]              # 재성 (내가 극하는 오행)
    authority_element = CONTROLLED_BY[user_element]      # 관성 (나를 극하는 오행)

    support_score = weighted[user_element] + weighted[supporting_element]  # 비겁 + 인성
    drain_score = (
        weighted[output_element]
        + weighted[wealth_element]
        + weighted[authority_element]
    )  # 식상 + 재성 + 관성

    return "신강" if support_score >= drain_score else "신약"


def get_yongsin_element(saju: dict) -> str:
    """
    억부법(抑扶法)을 기준으로 용신 후보 오행을 계산한다.

    현재 구현은 신강/신약에 따른 가장 기본적인 억부 원칙만 적용한다.

    - 신강: 일간을 극하는 오행(관성)을 용신 후보로 사용하여
      넘치는 기운을 제어한다.
    - 신약: 일간을 생조하는 오행(인성)을 용신 후보로 사용하여
      부족한 기운을 보완한다.

    실제 명리학에서의 용신 선정은
    - 조후(調候)
    - 격국(格局)
    - 통관(通關)
    - 병약(病藥)
    등을 종합적으로 고려하는 별도의 해석 체계를 필요로 하며,
    본 프로젝트의 현재 범위에는 포함하지 않는다.

    이 함수가 참조하는 신강/신약 판정(get_day_master_strength())은
    통근, 월령, 진술축미 토왕 보정을 반영하여 개선된 결과를 사용한다.

    TODO
    - 조후 기반 용신 검토
    - 격국 기반 용신 검토
    - 통관 관점의 용신 검토
    - 병약 관점의 용신 검토
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
    ※ 2장 전면 재검토 당시 이 방식을 다시 검토했으나, 초기/중기까지
      반영하는 대안은 정확도 향상 근거가 불명확하고 이미 신한은행과
      실측 검증된 결과(십성 7개 항목 일치)를 훼손할 위험이 있어
      현행(정기만 사용) 유지로 결정함.
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

    if not os.path.exists(_CSV_PATH):
        raise FileNotFoundError(
            f"절기 데이터 파일을 찾을 수 없습니다: {_CSV_PATH}\n"
            f"sajupy 패키지 버전이 바뀌면서 내부 파일 구조가 변경되었을 수 있습니다. "
            f"'pip show sajupy'로 설치된 버전을 확인하거나, "
            f"패키지를 재설치(pip install --force-reinstall sajupy)해보세요."
        )

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

    # 대운 시작 나이는 절기까지 남은 일수를 3으로 나눈 몫을 취하고,
    # 나머지(3일 미만의 남는 시간)는 버린다(절사). 이는 "3일을 온전히
    # 채워야 1년으로 인정한다"는 전통 명리학의 통상적 해석에 따른 것으로,
    # round()가 아닌 floor() 방식이 문헌상 더 널리 통용됨.
    # ※ 2장 재검토 당시, 방향(순행/역행) 판단을 반영한 정확한 경계값
    #   테스트 결과 test1~4 모두 raw<1 구간에 있어 round/floor 최종
    #   결과가 우연히 동일했음(0세→1세 보정 규칙으로 수렴). 다만 floor가
    #   전통 문헌상 통상적으로 통용되는 절사 방식이라는 근거에 따라
    #   round에서 floor로 변경함 — 향후 raw≥1이면서 소수부가 0.5를
    #   넘는 케이스에서는 두 방식이 실제로 다른 결과를 낼 수 있음.
    # ※ GPT 지적대로 "서비스마다 다르다"는 점은 유의 — floor가 명리학계의
    #   유일한 정답은 아니며, 가장 널리 통용되는 해석을 채택한 것.
    start_age = int(delta_days / 3)  # floor: 소수점 이하 절사
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