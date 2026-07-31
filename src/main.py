"""
터미널 실행 진입점.
- 사용자로부터 생년월일시, 양력/음력 여부, 성별을 입력받아
  saju/calculator.py로 사주를 계산하고, llm/fortune_generator.py로
  오늘의 운세 해석을 생성해서 출력한다.
- 이 파일은 이미 만들어진 계산/해석 로직을 "조립"만 하는 역할이라,
  calculator.py / prompts.py / fortune_generator.py는 수정하지 않음.
"""

from src.saju.calculator import get_saju, get_saju_from_lunar, format_saju_summary
from src.llm.fortune_generator import generate_fortune


def get_int_input(prompt: str) -> int:
    """
    숫자 입력을 받되, 숫자가 아닌 값이 들어오면 다시 입력받음.
    """
    while True:
        value = input(prompt).strip()
        if value.isdigit():
            return int(value)
        print("숫자로 입력해주세요.")


def get_choice_input(prompt: str, options: list) -> str:
    """
    정해진 선택지 중 하나를 입력받되, 목록에 없는 값이 들어오면 다시 입력받음.
    """
    while True:
        value = input(prompt).strip()
        if value in options:
            return value
        print(f"{'/'.join(options)} 중 하나로 입력해주세요.")


def main():
    print("=== Kiwoon — 오늘의 운세 (터미널 버전) ===\n")

    calendar_type = get_choice_input("양력/음력 중 선택하세요 (양력/음력): ", ["양력", "음력"])
    year = get_int_input("태어난 연도 (예: 1990): ")
    month = get_int_input("태어난 월 (예: 10): ")
    day = get_int_input("태어난 일 (예: 10): ")
    hour = get_int_input("태어난 시 (24시간 기준, 예: 14): ")
    minute = get_int_input("태어난 분 (예: 30, 모르면 0): ")
    gender = get_choice_input("성별을 입력하세요 (남성/여성): ", ["남성", "여성"])

    if calendar_type == "음력":
        saju = get_saju_from_lunar(year, month, day, hour, minute)
    else:
        saju = get_saju(year, month, day, hour, minute)

    summary = format_saju_summary(saju)

    print("\n[사주 정보]")
    print(summary)

    print("\n[오늘의 운세]")
    print(generate_fortune(saju, summary, gender=gender))


if __name__ == "__main__":
    main()