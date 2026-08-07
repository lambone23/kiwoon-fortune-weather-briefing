"""
2장 전면 재검토 최종 회귀 테스트.
- test_saju.py의 4개 케이스(sajuinfo.co.kr 원국 대조용)를 재사용하여,
  2-2~2-9에서 개선한 모든 로직(지장간, 왕상휴수사, 통근, 월령, 토왕,
  용신, 대운 절사)이 적용된 상태에서 십성·대운·신강신약·용신까지
  종합 확인.
- test1(1990-10-10 14:30, 여성)은 신한은행과 실측 대조된 유일한
  기준 케이스 — 십성 7개, 대운 10개가 여전히 일치하는지가 핵심 검증.
- test2~4는 원국만 검증되어 있던 경계 케이스라, 이번이 십성/대운/
  신강신약/용신까지 처음으로 확인하는 자리.
"""

from src.saju.calculator import (
    get_saju, format_saju_summary,
    get_weighted_element_distribution, get_day_master_strength,
    get_lucky_info, format_lucky_info,
    get_ten_gods_summary, format_ten_gods_summary,
    get_daeun, format_daeun_summary,
)

# test_saju.py와 동일한 4개 케이스 (생년월일시만 재사용, gender는
# 대운 방향 계산에 필요해 임의로 여성 지정 — 방향 로직 자체 검증 목적)
TEST_CASES = [
    ("test1: 일반 케이스 (신한 대조 기준)", 1990, 10, 10, 14, 30, "여성"),
    ("test2: 자시 경계 (夜子時)", 1990, 10, 10, 23, 30, "여성"),
    ("test3: 절기 경계 - 입춘 전날", 1990, 2, 3, 14, 30, "여성"),
    ("test4: 절기 경계 - 입춘 이후", 1990, 2, 5, 14, 30, "여성"),
]

# test1의 신한은행 실측 기준값 (인계 문서 기준)
EXPECTED_TEST1_TEN_GODS = {
    "년간": "식신", "월간": "편인", "시간": "겁재",
    "년지": "정인", "월지": "비견", "일지": "식신", "시지": "겁재",
}
EXPECTED_TEST1_DAEUN_START_AGE = 1
EXPECTED_TEST1_DAEUN_FIRST_GANZHI = "乙酉"


def run_case(label, year, month, day, hour, minute, gender):
    print(f"\n{'='*60}\n[{label}]\n{'='*60}")
    saju = get_saju(year, month, day, hour, minute)
    print(format_saju_summary(saju))

    weighted = get_weighted_element_distribution(saju)
    print(f"\n계절 가중 오행 분포: { {k: round(v, 2) for k, v in weighted.items()} }")

    strength = get_day_master_strength(saju)
    print(f"신강/신약: {strength}")

    lucky = get_lucky_info(saju)
    print(format_lucky_info(lucky))

    ten_gods = get_ten_gods_summary(saju)
    print("\n[십성]")
    print(format_ten_gods_summary(ten_gods))

    daeun = get_daeun(saju, year, month, day, hour, minute, gender=gender, periods=10)
    print("\n[대운]")
    print(format_daeun_summary(daeun))

    return {"saju": saju, "weighted": weighted, "strength": strength,
            "lucky": lucky, "ten_gods": ten_gods, "daeun": daeun}


if __name__ == "__main__":
    results = {}
    for label, year, month, day, hour, minute, gender in TEST_CASES:
        results[label] = run_case(label, year, month, day, hour, minute, gender)

    # test1 신한 대조 재확인
    print(f"\n{'='*60}\n[test1 신한은행 재대조 결과]\n{'='*60}")
    test1_result = results["test1: 일반 케이스 (신한 대조 기준)"]

    ten_gods_match = test1_result["ten_gods"] == EXPECTED_TEST1_TEN_GODS
    print(f"십성 7개 항목 일치: {'✅ PASS' if ten_gods_match else '❌ FAIL'}")
    if not ten_gods_match:
        for key in EXPECTED_TEST1_TEN_GODS:
            expected = EXPECTED_TEST1_TEN_GODS[key]
            actual = test1_result["ten_gods"][key]
            if expected != actual:
                print(f"  - {key}: 기대값={expected}, 실제값={actual}")

    daeun = test1_result["daeun"]
    start_age_match = daeun["start_age"] == EXPECTED_TEST1_DAEUN_START_AGE
    first_ganzhi_match = daeun["periods"][0]["ganzhi"] == EXPECTED_TEST1_DAEUN_FIRST_GANZHI

    start_age_status = "✅ PASS" if start_age_match else f"❌ FAIL (실제={daeun['start_age']})"
    first_ganzhi_status = "✅ PASS" if first_ganzhi_match else f"❌ FAIL (실제={daeun['periods'][0]['ganzhi']})"

    print(f"대운 시작 나이 일치({EXPECTED_TEST1_DAEUN_START_AGE}세): {start_age_status}")
    print(f"대운 첫 간지 일치({EXPECTED_TEST1_DAEUN_FIRST_GANZHI}): {first_ganzhi_status}")