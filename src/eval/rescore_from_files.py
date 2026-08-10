"""
이미 생성된 output_샘플*.txt 파일들을 다시 읽어서, 수정된
rule_check.py 로직으로 재채점. LLM을 다시 호출하지 않음
(3-4-3에서 rule_check.py를 수정한 뒤, 3-3에서 생성한 50개 원문에
 새 로직만 재적용하기 위한 스크립트).
- 콘솔 출력은 터미널 버퍼 문제로 잘릴 수 있으므로, 채점 결과를
  파일로도 저장한다.
"""

import re
import io
import contextlib
from src.saju.calculator import get_saju, get_lucky_info
from src.eval.rule_check import run_tier1_check, print_report

SAMPLES = [
    {"label": "샘플1", "year": 1990, "month": 10, "day": 10, "hour": 14, "minute": 30},
    {"label": "샘플2", "year": 1985, "month": 11, "day": 11, "hour": 6, "minute": 0},
    {"label": "샘플3", "year": 1995, "month": 7, "day": 20, "hour": 15, "minute": 0},
    {"label": "샘플4", "year": 1990, "month": 5, "day": 5, "hour": 9, "minute": 0},
    {"label": "샘플5", "year": 2000, "month": 1, "day": 15, "hour": 22, "minute": 0},
]


def extract_results(filepath: str) -> list[str]:
    """저장된 파일에서 [N번째 결과] 구간별 원문만 추출."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r"=+\n\[\d+번째 결과\]\n=+\n", content)
    return [b.strip() for b in blocks[1:] if b.strip()]


def is_all_pass(report: dict) -> bool:
    """report 딕셔너리 전체가 PASS인지 확인."""
    checks = [
        report["labels_in_order"]["pass"],
        report["no_markdown"]["pass"],
        report["no_hanja"]["pass"],
        report["no_forbidden_terms"]["pass"],
        report["lucky_info_match"]["color_pass"],
        report["lucky_info_match"]["direction_pass"],
        report["lucky_info_match"]["material_pass"],
    ]
    checks += [v["pass"] for v in report["sentence_counts"].values()]
    return all(checks)


if __name__ == "__main__":
    total_pass = 0
    total_count = 0
    summary_lines = []

    output_path = "src/eval/rescore_result.txt"
    with open(output_path, "w", encoding="utf-8") as out_f:
        for sample in SAMPLES:
            saju = get_saju(sample["year"], sample["month"], sample["day"],
                             sample["hour"], sample["minute"])
            lucky = get_lucky_info(saju)

            filepath = f"src/eval/output_{sample['label']}.txt"
            results = extract_results(filepath)

            header = f"\n{'#'*60}\n{sample['label']} 재채점 ({len(results)}개)\n{'#'*60}\n"
            print(header)
            out_f.write(header)

            sample_pass = 0
            for i, fortune in enumerate(results, 1):
                report = run_tier1_check(fortune, lucky)

                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    print_report(report, index=i)
                captured = buf.getvalue()

                print(captured)
                out_f.write(captured + "\n")

                if is_all_pass(report):
                    sample_pass += 1
                total_count += 1

            total_pass += sample_pass
            line = f"\n[{sample['label']}] {sample_pass}/{len(results)} PASS\n"
            print(line)
            out_f.write(line)
            summary_lines.append(f"{sample['label']}: {sample_pass}/{len(results)} PASS")

        footer = f"\n{'#'*60}\n전체 재채점 완료: {total_pass}/{total_count} PASS\n{'#'*60}\n"
        footer += "\n[사주별 요약]\n" + "\n".join(summary_lines) + "\n"
        print(footer)
        out_f.write(footer)

    print(f"\n결과 저장 완료: {output_path}")