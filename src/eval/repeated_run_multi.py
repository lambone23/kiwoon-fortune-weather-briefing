"""
본과정(3장) 전용: 5개 사주 샘플 × 10회 반복 실행.
- 1장(초기 점검)의 repeated_run.py(1개 사주 × 20회)와 달리,
  5개 사주 각각에 대해 10회씩 반복해서 사주 다양성을 확보.
- 결과는 사주별로 별도 파일에 저장되어, Tier 1 채점과 Tier 2 Judge에
  각각 활용됨.
"""

from datetime import date
from src.saju.calculator import get_saju, format_saju_summary, get_lucky_info
from src.llm.fortune_generator import generate_fortune
from src.eval.rule_check import run_tier1_check, print_report

# 3-2에서 확정한 5개 사주 샘플
SAMPLES = [
    {"label": "샘플1", "year": 1990, "month": 10, "day": 10, "hour": 14, "minute": 30, "gender": "여성"},
    {"label": "샘플2", "year": 1985, "month": 11, "day": 11, "hour": 6, "minute": 0, "gender": "여성"},
    {"label": "샘플3", "year": 1995, "month": 7, "day": 20, "hour": 15, "minute": 0, "gender": "남성"},
    {"label": "샘플4", "year": 1990, "month": 5, "day": 5, "hour": 9, "minute": 0, "gender": "여성"},
    {"label": "샘플5", "year": 2000, "month": 1, "day": 15, "hour": 22, "minute": 0, "gender": "남성"},
]

REPEAT_COUNT = 10


def run_sample_repeated(sample: dict, n: int = REPEAT_COUNT):
    saju = get_saju(sample["year"], sample["month"], sample["day"],
                     sample["hour"], sample["minute"])
    summary = format_saju_summary(saju)
    lucky = get_lucky_info(saju)

    results = []
    reports = []

    output_path = f"src/eval/output_{sample['label']}.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"[{sample['label']}] {sample['year']}-{sample['month']:02d}-{sample['day']:02d} "
                 f"{sample['hour']:02d}:{sample['minute']:02d} ({sample['gender']})\n\n")
        f.write(f"{summary}\n\n")
        f.write(f"[행운 정보 - 정답]\n컬러: {lucky['color']} / 방향: {lucky['direction']} / 소재: {lucky['material']}\n\n")

        for i in range(1, n + 1):
            fortune = generate_fortune(saju, summary, today=date.today(), gender=sample["gender"])
            results.append(fortune)

            report = run_tier1_check(fortune, lucky)
            reports.append(report)
            print_report(report, index=i)

            f.write(f"{'='*50}\n[{i}번째 결과]\n{'='*50}\n{fortune}\n\n")

    print(f"\n[{sample['label']}] 저장 완료: {output_path}\n")
    return results, reports


if __name__ == "__main__":
    all_results = {}
    all_reports = {}

    for sample in SAMPLES:
        print(f"\n{'#'*60}\n{sample['label']} 실행 시작\n{'#'*60}")
        results, reports = run_sample_repeated(sample)
        all_results[sample["label"]] = results
        all_reports[sample["label"]] = reports

    print(f"\n{'#'*60}\n전체 완료: 5개 사주 × 10회 = {5*REPEAT_COUNT}개 결과 생성\n{'#'*60}")