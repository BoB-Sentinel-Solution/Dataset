#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_entity_spans.py
- JSONL의 각 객체에서 content와 entities[*]의 begin/end, value 일치 여부를 검증
- 체크 항목:
  1) content 존재 및 문자열 여부
  2) entities 존재 및 리스트 여부
  3) 각 엔티티에 value(str), label(str), begin(int), end(int) 존재
  4) 0 <= begin < end <= len(content)
  5) content[begin:end] == value (정확 일치)

- 실패 시: 첫 오류에서 즉시 종료(코드 1)
- 성공 시: 요약 출력 후 종료(코드 0)

옵션:
  --allow-empty-entities   : entities가 빈 리스트여도 오류로 보지 않음(기본: 빈 리스트면 통과, 항목이 있으면 모두 검증)
  --show-context N         : 매칭 실패 시 주변 N글자 컨텍스트를 함께 출력 (기본 12)
"""

import sys
import json
import argparse
from typing import Any, Dict, List

def parse_args():
    p = argparse.ArgumentParser(description="Validate begin/end spans against content in JSONL.")
    p.add_argument("-i", "--input", required=True, help="입력 JSONL 경로")
    p.add_argument("--allow-empty-entities", action="store_true",
                   help="entities가 빈 리스트여도 허용(기본: 허용)")
    p.add_argument("--show-context", type=int, default=12,
                   help="불일치 시 앞뒤로 보여줄 컨텍스트 길이 (기본: 12)")
    return p.parse_args()

def excerpt(s: str, a: int, b: int, ctx: int) -> str:
    """content에서 [a:b] 주변 컨텍스트를 표시용으로 잘라 하이라이트"""
    start = max(0, a - ctx)
    end   = min(len(s), b + ctx)
    left  = s[start:a]
    mid   = s[a:b]
    right = s[b:end]
    return f"{left}⟦{mid}⟧{right}"

def validate_record(obj: Dict[str, Any], lineno: int, ctx: int, allow_empty_entities: bool) -> None:
    # content
    if "content" not in obj or not isinstance(obj["content"], str):
        raise ValueError(f"[라인 {lineno}] 'content'가 없거나 문자열이 아닙니다.")
    content = obj["content"]

    # entities
    ents = obj.get("entities", None)
    if ents is None:
        raise ValueError(f"[라인 {lineno}] 'entities' 키가 없습니다.")
    if not isinstance(ents, list):
        raise ValueError(f"[라인 {lineno}] 'entities'가 리스트가 아닙니다.")

    if len(ents) == 0 and not allow_empty_entities:
        # 기본은 빈 리스트도 허용하지만, 옵션을 끄지 않았다면 경고/오류로 다룰 수도 있음.
        # 여기서는 옵션 미사용 시에도 통과로 둡니다.
        pass

    # 각 엔티티 검증
    for idx, ent in enumerate(ents):
        if not isinstance(ent, dict):
            raise ValueError(f"[라인 {lineno}] entities[{idx}]가 객체가 아닙니다.")

        for k in ("value", "label", "begin", "end"):
            if k not in ent:
                raise ValueError(f"[라인 {lineno}] entities[{idx}]에 '{k}' 키가 없습니다.")

        value = ent["value"]
        label = ent["label"]
        begin = ent["begin"]
        end   = ent["end"]

        if not isinstance(value, str):
            raise ValueError(f"[라인 {lineno}] entities[{idx}].value 타입 오류(문자열 아님)")
        if not isinstance(label, str):
            raise ValueError(f"[라인 {lineno}] entities[{idx}].label 타입 오류(문자열 아님)")
        if not isinstance(begin, int) or not isinstance(end, int):
            raise ValueError(f"[라인 {lineno}] entities[{idx}].begin/end 타입 오류(정수 아님)")
        if begin >= end:
            raise ValueError(f"[라인 {lineno}] entities[{idx}] 범위 오류: begin({begin}) >= end({end})")

        n = len(content)
        if not (0 <= begin < end <= n):
            raise ValueError(
                f"[라인 {lineno}] entities[{idx}] 범위 초과: begin={begin}, end={end}, len(content)={n}"
            )

        slice_text = content[begin:end]
        if slice_text != value:
            # 불일치 상세 안내
            around = excerpt(content, begin, end, ctx)
            raise ValueError(
                (f"[라인 {lineno}] entities[{idx}] 값 불일치\n"
                 f"  label = {label}\n"
                 f"  value = {value!r}\n"
                 f"  slice = {slice_text!r}  (content[{begin}:{end}])\n"
                 f"  context: …{around}…")
            )

def main():
    args = parse_args()
    total = 0
    with open(args.input, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            total += 1
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[에러] {lineno}번째 줄 JSON 파싱 실패: {e}\n")
                sys.exit(1)

            if not isinstance(obj, dict):
                sys.stderr.write(f"[에러] {lineno}번째 줄 최상위 JSON이 객체가 아닙니다.\n")
                sys.exit(1)

            try:
                validate_record(obj, lineno, args.show_context, args.allow_empty_entities)
            except ValueError as e:
                sys.stderr.write(str(e) + "\n")
                sys.exit(1)

    sys.stderr.write(f"[검증 성공] 총 {total}건 검사 완료. 모든 begin/end와 value가 content와 일치합니다.\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
