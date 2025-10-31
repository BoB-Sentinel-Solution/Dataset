#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
renumber_jsonl_ids.py
- JSONL을 위에서부터 읽어 각 객체의 `id`를 1,2,3,... 순으로 재부여
- 기본은 기존 id를 덮어씀. --preserve-original 사용 시 기존 id를 orig_id로 보존
- 라인 단위 스트리밍 처리
"""

import sys
import json
import argparse

def parse_args():
    p = argparse.ArgumentParser(description="Renumber `id` fields sequentially in JSONL.")
    p.add_argument("-i", "--input", required=True, help="입력 JSONL 경로")
    p.add_argument("-o", "--output", required=True, help="출력 JSONL 경로")
    p.add_argument("--preserve-original", action="store_true",
                   help="기존 id를 orig_id로 보존")
    return p.parse_args()

def main():
    args = parse_args()
    next_id = 1
    total, written = 0, 0

    with open(args.input, "r", encoding="utf-8") as fin, \
         open(args.output, "w", encoding="utf-8") as fout:
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

            if not isinstance(obj, dict):
                sys.stderr.write(f"[경고] {lineno}번째 줄 최상위 JSON이 객체가 아님: 건너뜀\n")
                continue

            if args.preserve_original and "id" in obj:
                obj["orig_id"] = obj["id"]

            obj["id"] = next_id
            next_id += 1

            fout.write(json.dumps(obj, ensure_ascii=False))
            fout.write("\n")
            written += 1

    sys.stderr.write(f"[정보] 입력 {total}건 처리, 출력 {written}건, 최종 id={next_id-1}\n")

if __name__ == "__main__":
    main()
