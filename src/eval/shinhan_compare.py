"""
신한은행 '오늘의 운세'와 대조하기 위한 5개 사주 샘플 실행 스크립트.
- 신한 사이트에서 실제로 조회한 날짜를 직접 지정해서 generate_fortune()을
  호출, 결과를 나란히 비교할 수 있도록 출력.
- 결과는 날짜별 텍스트 파일로 저장되어 LLM Judge에게 그대로 붙여넣기 가능
  (5일치를 각각 구분해서 보관하기 위해 파일명에 날짜를 포함).
"""

from datetime import date
from src.saju.calculator import get_saju, format_saju_summary, get_lucky_info
from src.llm.fortune_generator import generate_fortune

# 3-2에서 확정한 5개 사주 샘플 (3-3, 3-4와 동일한 샘플 재사용)
SAMPLES = [
    {"label": "샘플1", "year": 1990, "month": 10, "day": 10, "hour": 14, "minute": 30, "gender": "여성"},
    {"label": "샘플2", "year": 1985, "month": 11, "day": 11, "hour": 6, "minute": 0, "gender": "여성"},
    {"label": "샘플3", "year": 1995, "month": 7, "day": 20, "hour": 15, "minute": 0, "gender": "남성"},
    {"label": "샘플4", "year": 1990, "month": 5, "day": 5, "hour": 9, "minute": 0, "gender": "여성"},
    {"label": "샘플5", "year": 2000, "month": 1, "day": 15, "hour": 22, "minute": 0, "gender": "남성"},
]


def run_sample(sample: dict, target_date: date) -> str:
    saju = get_saju(sample["year"], sample["month"], sample["day"],
                     sample["hour"], sample["minute"])
    summary = format_saju_summary(saju)
    lucky = get_lucky_info(saju)

    fortune_text = generate_fortune(saju, summary, today=target_date, gender=sample["gender"])

    header = (
        f"{'='*60}\n"
        f"[{sample['label']}] {sample['year']}-{sample['month']:02d}-{sample['day']:02d} "
        f"{sample['hour']:02d}:{sample['minute']:02d} ({sample['gender']})\n"
        f"기준 날짜: {target_date.strftime('%Y-%m-%d')}\n"
        f"{'='*60}\n"
    )
    body = f"{summary}\n\n행운 오행: {lucky['element']} / {lucky['color']} / {lucky['direction']} / {lucky['material']}\n\n{fortune_text}\n"
    return header + body


if __name__ == "__main__":
    # ── 신한 사이트에서 실제로 조회한 날짜를 여기에 직접 입력 ──
    TARGET_DATE = date(2026, 8, 11)   # 예시: 2026년 8월 9일

    print(f"기준 날짜: {TARGET_DATE.strftime('%Y-%m-%d')}\n")

    all_results = []
    for sample in SAMPLES:
        result = run_sample(sample, TARGET_DATE)
        print(result)
        all_results.append(result)

    output_filename = f"src/eval/shinhan_compare_output_{TARGET_DATE.strftime('%Y%m%d')}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(f"기준 날짜: {TARGET_DATE.strftime('%Y-%m-%d')}\n\n")
        f.write("\n".join(all_results))

    print(f"\n결과 저장 완료: {output_filename}")