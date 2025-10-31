#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_entity_spans.py
- JSONL 각 레코드의 entities[*].begin/end를 content와 value에 맞춰 자동 보정
- 동작:
  1) content[begin:end] == value 면 유지
  2) 아니면 content 내 value의 모든 발생 위치 후보를 수집
  3) 기존 begin과의 거리(|candidate_begin - old_begin|)가 최소인 후보를 선택
  4) (기본) 이미 배정된 스팬과 겹치지 않도록 후보 중 비겹침 우선 선택
  5) 보정 실패 시 경고 출력(원래 값 유지)

옵션:
  -i / -o : 입력/출력 JSONL 경로(필수)
  --allow-overlap : 스팬 겹침 허용 (기본: 금지)
  --dry-run       : 파일에 쓰지 않고 변경 요약만 출력
  --report        : 변경 상세 리포트 출력(표준에러)
  --strict        : 보정 실패 시 즉시 종료(기본: 경고만)
"""

import sys
import json
import argparse
from typing import List, Tuple, Dict, Any

def parse_args():
    p = argparse.ArgumentParser(description="Auto-fix entity begin/end spans using content & value.")
    p.add_argument("-i", "--input", required=True, help="입력 JSONL 경로")
    p.add_argument("-o", "--output", required=False, help="출력 JSONL 경로 (dry-run이면 생략 가능)")
    p.add_argument("--allow-overlap", action="store_true", help="스팬 겹침 허용")
    p.add_argument("--dry-run", action="store_true", help="파일 기록 없이 변경 내역만 출력")
    p.add_argument("--report", action="store_true", help="변경 상세 리포트 출력")
    p.add_argument("--strict", action="store_true", help="보정 실패 시 즉시 종료")
    return p.parse_args()

def find_all(hay: str, needle: str) -> List[int]:
    """hay에서 needle의 모든 시작 인덱스 반환 (겹침 허용)"""
    if not needle:
        return []
    res = []
    i = hay.find(needle)
    while i != -1:
        res.append(i)
        i = hay.find(needle, i + 1)
    return res

def overlaps(a: Tuple[int,int], b: Tuple[int,int]) -> bool:
    """구간 a,b가 겹치면 True"""
    (a1,a2), (b1,b2) = a, b
    return not (a2 <= b1 or b2 <= a1)

def choose_best_candidate(cands: List[int], old_begin: int, used: List[Tuple[int,int]], length: int, allow_overlap: bool) -> Tuple[int,int] | None:
    """후보 시작 인덱스들 중에서 기존 begin과의 거리 최소 & (기본) 비겹침을 만족하는 최적 후보 선택"""
    if not cands:
        return None
    # 1순위: 비겹침 후보 중 최단거리
    ranked = sorted(cands, key=lambda s: abs(s - (old_begin if old_begin is not None else 0)))
    if not allow_overlap:
        for s in ranked:
            span = (s, s + length)
            if all(not overlaps(span, u) for u in used):
                return span
    # 2순위: 겹침 허용 시 최단거리
    s = ranked[0]
    return (s, s + length)

def fix_record(obj: Dict[str, Any], allow_overlap: bool=False, report: bool=False) -> Tuple[Dict[str, Any], List[str], int, int]:
    """
    한 레코드의 스팬을 보정.
    반환: (수정된 객체, 로그 리스트, 수정개수, 실패개수)
    """
    logs: List[str] = []
    fixed, failed = 0, 0

    content = obj.get("content", None)
    ents = obj.get("entities", None)

    if not isinstance(content, str) or not isinstance(ents, list):
        return obj, logs, fixed, failed

    used_spans: List[Tuple[int,int]] = []
    # 먼저 기존에 올바른 스팬들을 선점(다른 엔티티와의 충돌 방지용)
    for idx, ent in enumerate(ents):
        if not isinstance(ent, dict):
            continue
        v = ent.get("value")
        b = ent.get("begin")
        e = ent.get("end")
        if isinstance(v, str) and isinstance(b, int) and isinstance(e, int):
            if 0 <= b < e <= len(content) and content[b:e] == v:
                used_spans.append((b, e))

    # 보정 루프
    for idx, ent in enumerate(ents):
        if not isinstance(ent, dict):
            continue
        v = ent.get("value")
        b = ent.get("begin")
        e = ent.get("end")
        label = ent.get("label")

        # 스키마 체크
        if not isinstance(v, str):
            continue

        ok_already = isinstance(b, int) and isinstance(e, int) and 0 <= b < e <= len(content) and content[b:e] == v
        if ok_already:
            # 이미 올바르면 패스(used에 이미 반영됨)
            continue

        # 후보 수집
        length = len(v)
        cands = find_all(content, v)

        # 기존 begin이 없거나 엉뚱하면 0으로 가까움 판단
        old_begin = b if isinstance(b, int) else 0

        span = choose_best_candidate(cands, old_begin, used_spans, length, allow_overlap)
        if span is None:
            failed += 1
            if report:
                logs.append(f"[WARN] id={obj.get('id')} ent#{idx} label={label} value={v!r} → 후보 없음(원본 begin/end 유지)")
            continue

        new_b, new_e = span
        # used 업데이트(비겹침 모드에서는 선택 시 이미 검증됨)
        used_spans.append((new_b, new_e))

        # 변경 기록
        if report:
            logs.append(
                f"[FIX ] id={obj.get('id')} ent#{idx} label={label} "
                f"old=({b},{e}) -> new=({new_b},{new_e}) "
                f"text='{content[new_b:new_e]}'"
            )

        ent["begin"] = new_b
        ent["end"]   = new_e
        fixed += 1

    return obj, logs, fixed, failed

def main():
    args = parse_args()
    if not args.dry_run and not args.output:
        sys.stderr.write("[에러] --dry-run이 아니면 --output을 지정해야 합니다.\n")
        sys.exit(1)

    total, total_fixed, total_failed = 0, 0, 0
    out_f = None
    if not args.dry_run:
        out_f = open(args.output, "w", encoding="utf-8")

    try:
        with open(args.input, "r", encoding="utf-8") as fin:
            for lineno, line in enumerate(fin, 1):
                s = line.strip()
                if not s:
                    continue
                total += 1
                try:
                    obj = json.loads(s)
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"[에러] {lineno}번째 줄 JSON 파싱 실패: {e}\n")
                    sys.exit(1)

                new_obj, logs, fixed, failed = fix_record(
                    obj, allow_overlap=args.allow_overlap, report=args.report
                )
                total_fixed += fixed
                total_failed += failed

                if args.report and logs:
                    for msg in logs:
                        sys.stderr.write(msg + "\n")

                if not args.dry_run:
                    out_f.write(json.dumps(new_obj, ensure_ascii=False))
                    out_f.write("\n")
    finally:
        if out_f:
            out_f.close()

    sys.stderr.write(f"[요약] 레코드 {total}건 처리, 보정 {total_fixed}개, 실패 {total_failed}개\n")
    if args.strict and total_failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
