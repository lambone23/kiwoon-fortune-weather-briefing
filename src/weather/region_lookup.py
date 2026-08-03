"""
지역명(시/도 + 구/군) → 기상청 격자 좌표(nx, ny) 변환 모듈.
- data.go.kr 참고문서에서 정제한 region_grid.csv를 모듈 로드 시 1회만 읽어
  메모리(딕셔너리)에 올려두고, 이후 조회는 전부 메모리 기반으로 처리.
"""

import csv
import os

_CSV_PATH = os.path.join(os.path.dirname(__file__), "region_grid.csv")
_region_map: dict[tuple[str, str], tuple[int, int]] = {}


def _load_region_data() -> None:
    """
    region_grid.csv를 읽어서 _region_map에 채워 넣음.
    모듈이 처음 import될 때 한 번만 호출됨.
    """
    with open(_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["region_1"], row["region_2"])
            _region_map[key] = (int(row["nx"]), int(row["ny"]))


_load_region_data()


def get_all_region_1() -> list[str]:
    """
    1단계(시/도) 목록을 중복 없이 반환. 프론트엔드 드롭다운 구성에 사용.
    """
    return sorted({key[0] for key in _region_map.keys()})


def get_region_2_list(region_1: str) -> list[str]:
    """
    특정 시/도에 속한 2단계(구/군) 목록을 반환. 프론트엔드 하위 드롭다운 구성에 사용.
    """
    return sorted(key[1] for key in _region_map.keys() if key[0] == region_1)


def get_coordinates(region_1: str, region_2: str) -> tuple[int, int]:
    """
    지역명(시/도, 구/군)을 받아서 기상청 격자 좌표(nx, ny)를 반환.

    Args:
        region_1: 시/도 (예: "서울특별시")
        region_2: 구/군 (예: "강남구")

    Returns:
        tuple[int, int]: (nx, ny)

    Raises:
        ValueError: 매핑되지 않는 지역명일 경우
    """
    key = (region_1, region_2)
    if key not in _region_map:
        raise ValueError(f"등록되지 않은 지역입니다: {region_1} {region_2}")
    return _region_map[key]


if __name__ == "__main__":
    print("전체 시/도 개수:", len(get_all_region_1()))
    print("서울특별시 목록 예시:", get_all_region_1()[:5])
    print()

    print("서울특별시 소속 구/군:", get_region_2_list("서울특별시")[:5])
    print()

    print("서울 강남구 좌표:", get_coordinates("서울특별시", "강남구"))
    print("부산 해운대구 좌표:", get_coordinates("부산광역시", "해운대구"))

    try:
        get_coordinates("서울특별시", "없는구")
    except ValueError as e:
        print("예외 처리 확인:", e)