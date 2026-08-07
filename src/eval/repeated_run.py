"""
동일 사주 입력으로 generate_fortune()을 N회 반복 실행.
- 결과를 콘솔에 출력 + 텍스트 파일로 저장 (LLM Judge에게 붙여넣기 편하도록)
- 각 결과에 Tier 1 자동 채점도 함께 실행.
"""

from datetime import date
from src.saju.calculator import get_saju, format_saju_summary, get_lucky_info
from src.llm.fortune_generator import generate_fortune
from src.eval.rule_check import run_tier1_check, print_report


def run_repeated(year: int, month: int, day: int, hour: int, minute: int,
                  gender: str, n: int = 5, output_path: str = None):
    saju = get_saju(year, month, day, hour, minute)
    summary = format_saju_summary(saju)
    lucky = get_lucky_info(saju)

    print(f"[사주 정보]\n{summary}\n")
    print(f"[행운 정보 - 정답]\n컬러: {lucky['color']} / 방향: {lucky['direction']} / 소재: {lucky['material']}\n")

    results = []
    all_reports = []

    for i in range(1, n + 1):
        fortune = generate_fortune(saju, summary, today=date.today(), gender=gender)
        results.append(fortune)

        report = run_tier1_check(fortune, lucky)
        all_reports.append(report)
        print_report(report, index=i)

        print(f"\n[{i}번째 원문]\n{fortune}\n")

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"[사주 정보]\n{summary}\n\n")
            f.write(f"[행운 정보 - 정답]\n컬러: {lucky['color']} / 방향: {lucky['direction']} / 소재: {lucky['material']}\n\n")
            for i, text in enumerate(results, 1):
                f.write(f"{'='*50}\n[{i}번째 결과]\n{'='*50}\n{text}\n\n")

    return results, all_reports


if __name__ == "__main__":
    # 케이스 1: 일반적인 케이스
    run_repeated(
        year=1990, month=10, day=10, hour=14, minute=30,
        gender="여성", n=20,
        output_path="src/eval/output_case1.txt",
    )