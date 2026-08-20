"""
LLM 호출 로직.
- prompts.py의 템플릿 + saju/calculator.py의 계산 결과(사용자 사주, 오늘 일진,
  행운 컬러/방향/소재)를 조합해서 OpenAI API(gpt-5-mini)를 호출,
  오늘의 운세 해석 텍스트를 생성.
"""

import os
from datetime import date
from dotenv import load_dotenv
from openai import OpenAI

from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.saju.calculator import (
    get_saju, get_lucky_info, format_lucky_info, get_saju_from_lunar,
    get_day_master_strength, get_ten_gods_summary, format_ten_gods_summary,
    get_ten_gods_distribution_summary,
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
    today_iljin = get_today_iljin(today)

    hour_known = saju.get("hour_known", True)

    lucky = get_lucky_info(saju)
    lucky_info = format_lucky_info(lucky)

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