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
    """전문용어(일간/십성/신강 등)가 설명 없이 그대로 노출되지 않았는지 확인."""
    found = [term for term in FORBIDDEN_TERMS if term in fortune_text]
    return {"pass": len(found) == 0, "found": found}


def check_lucky_info_matches(fortune_text: str, expected_color: str,
                              expected_direction: str, expected_material: str) -> dict:
    """
    행운 컬러/방향/소재가 calculator.py의 계산값과 일치하는지 확인.
    - expected_* 는 saju/calculator.py의 get_lucky_info() 결과를 그대로 사용.
    - 컬러/소재는 문구가 여러 단어라 핵심 키워드(첫 단어) 포함 여부로 판정.
    """
    def extract_section(label: str) -> str:
        match = re.search(rf"{label}\s*:\s*(.+?)(?=\n|$)", fortune_text)
        return match.group(1) if match else ""

    color_section = extract_section("행운 컬러")
    direction_section = extract_section("행운 방향")
    material_section = extract_section("행운 소재")

    color_key = expected_color.split("·")[0].replace(" 계열", "")
    material_key = expected_material.split(" ")[0]

    return {
        "color_pass": color_key in color_section,
        "direction_pass": expected_direction in direction_section,
        "material_pass": material_key in material_section,
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


def run_tier1_check(fortune_text: str, lucky: dict) -> dict:
    """Tier 1 전체 검사를 한 번에 실행."""
    return {
        "labels_in_order": check_all_labels_present_in_order(fortune_text),
        "no_markdown": check_no_markdown(fortune_text),
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