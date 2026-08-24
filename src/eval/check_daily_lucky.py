# 실행: python -m src.eval.check_daily_lucky  (프로젝트 루트 kiwoon 폴더에서)

"""
로컬 검증용 스크립트.
- 고정된 원국(사주) 하나를 기준으로, 여러 날짜에 대해
  '오늘의 행운 오행/컬러/방향/소재'가 실제로 날짜에 따라
  달라지는지 확인하기 위한 스크립트.
- 깃허브에는 올리지 않고 로컬 확인용으로만 사용.

실행 방법 (프로젝트 루트 kiwoon 폴더에서):
    python -m src.eval.check_daily_lucky
"""

from datetime import date, timedelta

from src.saju.calculator import (
    get_saju,
    get_day_master_strength,
    get_yongsin_element,
    get_yongsin_today_relation,
    get_today_lucky_info,
    STEM_TO_ELEMENT,
)


def check_date_range(saju: dict, start: date, days: int):
    """
    saju(고정 원국)에 대해 start부터 days일간, 오늘의 오행 관계와
    행운 컬러/방향/소재가 날짜별로 어떻게 나오는지 한 줄씩 출력.
    """
    base_element = STEM_TO_ELEMENT[saju["day_stem"]]
    strength = get_day_master_strength(saju)
    yongsin = get_yongsin_element(saju)

    print(f"[원국] 일간 오행: {base_element} / 신강신약: {strength} / 용신: {yongsin}")
    print("-" * 70)
    print(f"{'날짜':<12}{'오늘일진':<12}{'오늘오행':<8}{'관계':<6}{'행운컬러':<16}{'행운방향':<8}{'행운소재'}")
    print("-" * 70)

    seen_elements = set()

    for i in range(days):
        target_day = start + timedelta(days=i)
        today_saju = get_saju(target_day.year, target_day.month, target_day.day, 12, 0)
        today_element = STEM_TO_ELEMENT[today_saju["day_stem"]]
        relation = get_yongsin_today_relation(yongsin, today_element)
        lucky = get_today_lucky_info(saju, today_saju)

        seen_elements.add(lucky["element"])

        today_iljin = f"{today_saju['day_stem']}{today_saju['day_branch']}"
        print(
            f"{target_day.isoformat():<12}"
            f"{today_iljin:<12}"
            f"{today_element:<8}"
            f"{relation:<6}"
            f"{lucky['color']:<16}"
            f"{lucky['direction']:<8}"
            f"{lucky['material']}"
        )

    print("-" * 70)
    print(f"{days}일 중 등장한 행운 오행 종류: {sorted(seen_elements)} (총 {len(seen_elements)}종)")
    print()


if __name__ == "__main__":
    # ── 테스트 샘플: 필요하면 아래 값을 바꿔서 다른 원국으로도 확인 가능 ──
    # 샘플 1: 1990-10-10 14:30, 여성 (일간 토, 신강 예상)
    saju = get_saju(1990, 10, 10, 14, 30)

    # 샘플 2: 1995-07-20 15:00, 남성 (일간 수, 신약 예상) — 필요시 주석 해제
    # saju = get_saju(1995, 7, 20, 15, 0)

    # 오늘로부터 앞으로 30일치를 확인 (일진은 60갑자 주기라 60일을 봐야
    # 한 사이클이 다 도는데, 5가지 관계가 골고루 섞여 나오는지 보는
    # 용도로는 30일이면 충분히 확인 가능)
    check_date_range(saju, date.today(), days=30)

    # 60일(한 사이클)까지 보고 싶으면 아래 주석 해제
    # check_date_range(saju, date.today(), days=60)