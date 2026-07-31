"""
sajupy 계산 검증 스크립트.
- 1-11에서 sajuinfo.co.kr과 대조 검증했던 4가지 케이스를 코드로 정리.
- 계산 로직(sajupy 버전, 옵션 등)을 바꿀 때마다 이 스크립트로 재검증.
"""

from src.saju.calculator import get_saju, format_saju_summary


def run_test(label: str, year: int, month: int, day: int, hour: int, minute: int,
             expected: dict):
    saju = get_saju(year, month, day, hour, minute)

    print(f"\n=== {label} ===")
    print(f"입력: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
    print(format_saju_summary(saju))

    # 기대값(사주인포 등 외부 사이트 대조 결과)과 비교
    mismatches = []
    for key, expected_value in expected.items():
        if saju.get(key) != expected_value:
            mismatches.append(f"{key}: 기대값={expected_value}, 실제값={saju.get(key)}")

    if mismatches:
        print("❌ 불일치 발견:")
        for m in mismatches:
            print(f"  - {m}")
    else:
        print("✅ 외부 사이트(sajuinfo.co.kr) 결과와 일치")


if __name__ == "__main__":
    # test1: 일반 케이스
    run_test(
        "test1: 일반 케이스",
        1990, 10, 10, 14, 30,
        expected={
            "year_pillar": "庚午", "month_pillar": "丙戌",
            "day_pillar": "戊申", "hour_pillar": "己未",
        },
    )

    # test2: 자시 경계 (23시~01시 출생, 夜子時)
    run_test(
        "test2: 자시 경계 (夜子時)",
        1990, 10, 10, 23, 30,
        expected={
            "year_pillar": "庚午", "month_pillar": "丙戌",
            "day_pillar": "戊申", "hour_pillar": "甲子",
        },
    )

    # test3: 절기 경계 - 입춘 전날 (1990년 입춘은 2/4 무렵)
    run_test(
        "test3: 절기 경계 - 입춘 전날",
        1990, 2, 3, 14, 30,
        expected={
            "year_pillar": "己巳", "month_pillar": "丁丑",
            "day_pillar": "己亥", "hour_pillar": "辛未",
        },
    )

    # test4: 절기 경계 - 입춘 이후
    run_test(
        "test4: 절기 경계 - 입춘 이후",
        1990, 2, 5, 14, 30,
        expected={
            "year_pillar": "庚午", "month_pillar": "戊寅",
            "day_pillar": "辛丑", "hour_pillar": "乙未",
        },
    )