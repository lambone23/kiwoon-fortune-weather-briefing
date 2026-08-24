"""
LLM 호출 로직.
- prompts.py의 템플릿 + saju/calculator.py의 계산 결과(사용자 사주, 오늘 일진,
  행운 컬러/방향/소재)를 조합해서 OpenAI API(gpt-5-mini)를 호출,
  오늘의 운세 해석 텍스트를 생성.

[고도화 내역 - 3차]
- get_lucky_info()/format_lucky_info() 대신 get_today_lucky_info()/
  format_today_lucky_info()를 사용하도록 변경. 원국(saju)뿐 아니라
  오늘 날짜 기준 사주(today_saju)도 함께 넘겨서, 행운 컬러/방향/소재가
  오늘의 일진을 반영해 계산되도록 함. 자세한 배경은
  saju/calculator.py의 [고도화 내역 - 3차] 주석 참고.
- today_iljin 계산에 쓰던 today_saju 객체를 그대로 재사용해서
  get_saju() 중복 호출을 피함.

[고도화 내역 - 4차]
- 학업운 방향(집중이 잘 되는지/산만해지는지 등)이 LLM 호출마다
  일관성 없이 뒤집히는 문제를 해결하기 위해, "오늘의 십성"을 코드에서
  결정론적으로 계산해서 프롬프트에 추가로 전달함.
- get_today_ten_god(saju, today_saju) 추가 호출: 원국 일간 기준으로
  오늘의 일간이 어떤 십성(편인/정인/식신/상관/비견/겁재/편재/정재/
  편관/정관)에 해당하는지 계산.
- build_user_prompt()에 today_ten_god 인자 추가. prompts.py의
  SYSTEM_PROMPT 규칙 12-1에서 이 값을 기준으로 학업운 방향을 판단하도록
  지시하므로, LLM이 매번 다른 방향으로 임의 판단하지 않고 오늘의
  십성 값에 따라 일관되게 서술하게 됨.
"""

import os
from datetime import date
from dotenv import load_dotenv
from openai import OpenAI

from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.saju.calculator import (
    get_saju, get_today_lucky_info, format_today_lucky_info, get_saju_from_lunar,
    get_day_master_strength, get_ten_gods_summary, format_ten_gods_summary,
    get_ten_gods_distribution_summary, get_today_ten_god,
)
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
if not OPENAI_MODEL:
    raise RuntimeError("환경변수 OPENAI_MODEL이 설정되지 않았습니다. .env 또는 Render 환경변수를 확인하세요.")

def get_today_iljin(today: date) -> str:
    """
    오늘 날짜의 일진(일주 간지)을 계산.
    시간은 정오(12:00) 고정 — 일진은 '그날의 일주'만 필요하므로 시간에 영향받지 않음.
    """
    saju = get_saju(today.year, today.month, today.day, 12, 0)
    return f"{saju['day_pillar']} ({saju['day_stem']}{saju['day_branch']})"


def generate_fortune(saju: dict, saju_summary: str, today: date = None,
                      gender: str = None) -> str:
    """
    사주 정보를 받아서 오늘의 운세 해석 텍스트를 생성.
    saju에 hour_known=False가 포함돼 있으면(생시 미상), LLM에게 시주 기반
    해석을 시도하지 말라는 지시를 프롬프트에 함께 전달함.

    Args:
        saju: saju/calculator.py의 get_saju() 결과 (사주 딕셔너리 전체)
        saju_summary: saju/calculator.py의 format_saju_summary() 결과
        today: 기준 날짜 (기본값: 오늘)
        gender: 사용자 성별 (예: "남성", "여성"). 없으면 생략 가능

    Returns:
        str: LLM이 생성한 운세 해석 텍스트
    """
    if today is None:
        today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    # 오늘의 일진 계산에 쓰는 사주를 한 번만 계산해서, 일진 표기와
    # 행운 컬러/방향/소재 계산(get_today_lucky_info), 오늘의 십성 계산
    # (get_today_ten_god) 양쪽에 재사용.
    today_saju = get_saju(today.year, today.month, today.day, 12, 0)
    today_iljin = f"{today_saju['day_pillar']} ({today_saju['day_stem']}{today_saju['day_branch']})"

    hour_known = saju.get("hour_known", True)

    lucky = get_today_lucky_info(saju, today_saju)
    lucky_info = format_today_lucky_info(lucky)

    today_ten_god = get_today_ten_god(saju, today_saju)

    strength = get_day_master_strength(saju)
    ten_gods_dict = get_ten_gods_summary(saju)
    ten_gods_summary = format_ten_gods_summary(ten_gods_dict)
    ten_gods_distribution = get_ten_gods_distribution_summary(ten_gods_dict)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(
                saju_summary, today_str, today_iljin, lucky_info, gender,
                strength=strength, ten_gods_summary=ten_gods_summary,
                ten_gods_distribution=ten_gods_distribution,
                hour_known=hour_known,
                today_ten_god=today_ten_god,
            )},
        ],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    from src.saju.calculator import format_saju_summary

    # ── 테스트 샘플 선택: 아래 중 하나만 주석 해제해서 실행 ──

    # 샘플 1: 1990-10-10 14:30, 여성 (일간 토, 신강)
    saju = get_saju(1990, 10, 10, 14, 30)
    gender = "여성"

    # 샘플 2: 1985-11-11 06:00, 여성 (일간 목, 신강 예상)
    #saju = get_saju(1985, 11, 11, 6, 0)
    #gender = "여성"

    # 샘플 3: 1995-07-20 15:00, 남성 (일간 수, 신약 예상)
    #saju = get_saju(1995, 7, 20, 15, 0)
    #gender = "남성"

    # 샘플 4: 1990-05-05 09:00, 여성 (일간 금, 신약 예상)
    #saju = get_saju(1990, 5, 5, 9, 0)
    #gender = "여성"

    # 샘플 5: 음력 1990-08-22 14:30, 여성 (양력 1990-10-10과 같은 날인지 확인용)
    #saju = get_saju_from_lunar(1990, 8, 22, 14, 30)
    #gender = "여성"

    summary = format_saju_summary(saju)

    print("[사주 정보]")
    print(summary)
    print()
    print("[오늘의 일진]")
    print(get_today_iljin(date.today()))
    print()
    print("[오늘의 운세]")
    print(generate_fortune(saju, summary, gender=gender))