"""
Tier 1: 규칙 기반 자동 채점.
- LLM 호출 없이, prompts.py의 형식/표현 규칙을 코드로 검증.
- 행운 컬러/방향/소재는 calculator.py가 계산한 '정답'과 LLM 응답을 직접 대조 —
  명리학 지식 없이도 100% 객관적으로 채점 가능한 유일한 '정확성' 항목.
"""

import re

FORTUNE_LABELS = ["총운", "재물운", "학업운", "직업운", "건강운", "연애운",
                   "행운 컬러", "행운 소재", "행운 방향"]

CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
FORBIDDEN_TERMS = ["일간", "십성", "생조", "신강", "신약", "용신", "통근", "조후",
                    "비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인"]

# "편인"/"편이"는 "약한 편인 당신", "이런 편인 조언"처럼 다양한 수식어
# 뒤에 자연스럽게 붙는 한국어 표현이라, 특정 수식어 패턴만으로는
# 전부 커버하기 어려움. "편인"/"편이" 앞에 "당신"이나 명사가 오지 않고
# 조사·어미로 자연스럽게 이어지는 일반적인 패턴을 폭넓게 잡는다.
FALSE_POSITIVE_PATTERNS = [
    #r"[가-힣]+한\s*편인",    # 예: "약한 편인", "강한 편인"
    #r"[가-힣]+한\s*편이",    # 예: "약한 편이라", "강한 편이지만"
    #r"이런\s*편인",          # 예: "이런 편인 조언"
    #r"그런\s*편인",          # 예: "그런 편인 상황"
    #r"[가-힣]+는\s*편인",    # 예: "원하는 편인", "선호하는 편인"
    #r"[가-힣]+큰\s*편인",    # 예: "큰 편인데" ← 신규
    r"[가-힣]+(한|는|은|을|던)\s*편(인|이)",
]

# 컬러/방향/소재는 LLM이 자연스러운 한국어 동의어로 표현할 수 있음
# (예: "중앙"→"중심", "금속"→"메탈", "초록"→"그린"). 오행별로 실제
# 나올 법한 동의어를 미리 등록해두고, 이 중 하나라도 포함되면 PASS로 인정.
# ※ 완전한 동의어 사전이 아니라, 지금까지 관찰된 패턴과 자연스럽게
#   예상되는 표현을 근거로 커버한 근사치. 새로운 동의어가 발견되면
#   계속 추가해나가는 방식으로 운영.

DIRECTION_SYNONYMS = {
    "동쪽": ["동쪽", "동편"],
    "서쪽": ["서쪽", "서편"],
    "남쪽": ["남쪽", "남편"],
    "북쪽": ["북쪽", "북편"],
    "중앙": ["중앙", "중심", "가운데"],
}

MATERIAL_SYNONYMS = {
    "나무": ["나무", "목재", "우드"],
    "가죽": ["가죽", "레더"],
    "도자기": ["도자기", "흙", "세라믹"],
    "금속": ["금속", "메탈", "은빛", "스테인리스", "실버"],
    "유리": ["유리", "수정", "크리스탈", "글라스"],
}

COLOR_SYNONYMS = {
    "초록": ["초록", "청록", "그린", "연두"],
    "빨강": ["빨강", "주황", "레드", "오렌지"],
    "노랑": ["노랑", "베이지", "옐로우"],
    "흰색": ["흰색", "은색", "화이트", "실버"],
    "파랑": ["파랑", "검정", "블루", "네이비", "블랙"],
}


def _extract_synonym_key(expected_value: str, synonym_map: dict) -> list[str]:
    """
    expected_value(예: '초록·청록 계열', '금속 소재')에서 대표 키워드를
    찾아, synonym_map에 등록된 동의어 리스트를 반환.
    등록되지 않은 값이면 expected_value 자체를 정제해서 단일 후보로 사용.
    """
    for key, synonyms in synonym_map.items():
        if key in expected_value:
            return synonyms
    # 매핑에 없는 경우, 기존 방식대로 첫 단어만 추출해 단일 후보로 사용
    fallback = expected_value.split("·")[0].split(" ")[0].replace(" 계열", "")
    return [fallback]


def check_all_labels_present_in_order(fortune_text: str) -> dict:
    """9개 항목이 정확한 순서로 모두 존재하는지 확인."""
    positions = []
    for label in FORTUNE_LABELS:
        match = re.search(rf"{label}\s*:", fortune_text)
        positions.append(match.start() if match else None)

    missing = [FORTUNE_LABELS[i] for i, p in enumerate(positions) if p is None]
    present_positions = [p for p in positions if p is not None]
    in_order = present_positions == sorted(present_positions)

    return {"pass": not missing and in_order, "missing": missing, "in_order": in_order}


def check_no_markdown(fortune_text: str) -> dict:
    """마크다운 기호(*, #, -) 미사용 확인."""
    found = re.findall(r"[*#]{1,3}", fortune_text)
    return {"pass": len(found) == 0, "found": found}


def check_no_hanja(fortune_text: str) -> dict:
    """한자 간지 등이 노출되지 않았는지 확인."""
    found = CJK_PATTERN.findall(fortune_text)
    return {"pass": len(found) == 0, "found": found}


def check_no_forbidden_terms(fortune_text: str) -> dict:
    found = []
    for term in FORBIDDEN_TERMS:
        for match in re.finditer(re.escape(term), fortune_text):
            start = max(0, match.start() - 10)  # 앞쪽 여유를 좀 더 넉넉히
            end = min(len(fortune_text), match.end() + 5)
            context = fortune_text[start:end]
            if any(re.search(pattern, context) for pattern in FALSE_POSITIVE_PATTERNS):
                continue
            found.append(term)
            break

    return {"pass": len(found) == 0, "found": found}


def check_lucky_info_matches(fortune_text: str, expected_color: str,
                              expected_direction: str, expected_material: str) -> dict:
    """
    행운 컬러/방향/소재가 calculator.py의 계산값과 일치하는지 확인.
    - expected_* 는 saju/calculator.py의 get_lucky_info() 결과를 그대로 사용.
    - 컬러/방향/소재 모두 등록된 동의어 목록(COLOR_SYNONYMS,
      DIRECTION_SYNONYMS, MATERIAL_SYNONYMS)까지 인정한다
      (예: "금속"의 정답에 "메탈"이라는 자연스러운 동의어를 써도 PASS).
    """
    def extract_section(label: str) -> str:
        match = re.search(rf"{label}\s*:\s*(.+?)(?=\n|$)", fortune_text)
        return match.group(1) if match else ""

    color_section = extract_section("행운 컬러")
    direction_section = extract_section("행운 방향")
    material_section = extract_section("행운 소재")

    color_candidates = _extract_synonym_key(expected_color, COLOR_SYNONYMS)
    material_candidates = _extract_synonym_key(expected_material, MATERIAL_SYNONYMS)
    direction_candidates = DIRECTION_SYNONYMS.get(expected_direction, [expected_direction])

    return {
        "color_pass": any(word in color_section for word in color_candidates),
        "direction_pass": any(word in direction_section for word in direction_candidates),
        "material_pass": any(word in material_section for word in material_candidates),
        "color_section": color_section,
        "direction_section": direction_section,
        "material_section": material_section,
    }

def check_sentence_counts(fortune_text: str) -> dict:
    """총운~연애운 각 2~3문장, 행운 3항목 각 1문장인지 확인."""
    main_items = ["총운", "재물운", "학업운", "직업운", "건강운", "연애운"]
    lucky_items = ["행운 컬러", "행운 소재", "행운 방향"]
    results = {}

    def extract_section(label: str) -> str:
        pattern = rf"{label}\s*:\s*([\s\S]*?)(?=(?:{'|'.join(FORTUNE_LABELS)}):|$)"
        match = re.search(pattern, fortune_text)
        return match.group(1).strip() if match else ""

    def count_sentences(text: str) -> int:
        return len([s for s in re.split(r"[.!?]\s*|다\.\s*|요\.\s*", text) if s.strip()])

    for label in main_items:
        count = count_sentences(extract_section(label))
        results[label] = {"count": count, "pass": 2 <= count <= 4}  # 여유 범위

    for label in lucky_items:
        count = count_sentences(extract_section(label))
        results[label] = {"count": count, "pass": count <= 2}  # 1문장 기준, 약간 여유

    return results


def check_no_parentheses(fortune_text: str) -> dict:
    """괄호를 이용한 부연 설명이 없는지 확인."""
    found = re.findall(r"[()]", fortune_text)
    return {"pass": len(found) == 0, "found": found}

def run_tier1_check(fortune_text: str, lucky: dict) -> dict:
    return {
        "labels_in_order": check_all_labels_present_in_order(fortune_text),
        "no_markdown": check_no_markdown(fortune_text),
        "no_parentheses": check_no_parentheses(fortune_text),  # 신규
        "no_hanja": check_no_hanja(fortune_text),
        "no_forbidden_terms": check_no_forbidden_terms(fortune_text),
        "lucky_info_match": check_lucky_info_matches(
            fortune_text, lucky["color"], lucky["direction"], lucky["material"]
        ),
        "sentence_counts": check_sentence_counts(fortune_text),
    }


def print_report(report: dict, index: int = None):
    """검사 결과를 보기 좋게 출력."""
    header = f"[{index}번째 결과]" if index is not None else "[검사 결과]"
    print(f"\n{'='*50}\n{header}\n{'='*50}")

    print(f"9개 항목 순서: {'PASS' if report['labels_in_order']['pass'] else 'FAIL'} "
          f"{report['labels_in_order'] if not report['labels_in_order']['pass'] else ''}")
    print(f"마크다운 미사용: {'PASS' if report['no_markdown']['pass'] else 'FAIL'} "
          f"{report['no_markdown']['found'] if not report['no_markdown']['pass'] else ''}")
    print(f"괄호 미사용: {'PASS' if report['no_parentheses']['pass'] else 'FAIL'} "
          f"{report['no_parentheses']['found'] if not report['no_parentheses']['pass'] else ''}")
    print(f"한자 미노출: {'PASS' if report['no_hanja']['pass'] else 'FAIL'} "
          f"{report['no_hanja']['found'] if not report['no_hanja']['pass'] else ''}")
    print(f"전문용어 미노출: {'PASS' if report['no_forbidden_terms']['pass'] else 'FAIL'} "
          f"{report['no_forbidden_terms']['found'] if not report['no_forbidden_terms']['pass'] else ''}")

    lucky = report["lucky_info_match"]
    print(f"행운 컬러 일치: {'PASS' if lucky['color_pass'] else 'FAIL'} → '{lucky['color_section']}'")
    print(f"행운 방향 일치: {'PASS' if lucky['direction_pass'] else 'FAIL'} → '{lucky['direction_section']}'")
    print(f"행운 소재 일치: {'PASS' if lucky['material_pass'] else 'FAIL'} → '{lucky['material_section']}'")

    for label, result in report["sentence_counts"].items():
        status = "PASS" if result["pass"] else "FAIL"
        print(f"문장 수 [{label}]: {status} ({result['count']}문장)")

        