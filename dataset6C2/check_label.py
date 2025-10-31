#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json

def main():
    if len(sys.argv) < 2:
        print("사용법: python show_entities.py <input.jsonl>")
        sys.exit(1)

    path = sys.argv[1]

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)
            _id = obj.get("id")
            entities = obj.get("entities", [])

            # value 최대 길이 찾아서 열 정렬
            value_width = 0
            for e in entities:
                v = e.get("value", "")
                value_width = max(value_width, len(v))

            print(f"ID: {_id}")
            print("-" * 30)
            if not entities:
                print("  (entities 없음)")
            else:
                # 헤더
                print(f"  {'VALUE'.ljust(value_width)}  | LABEL")
                print(f"  {'-' * value_width}  | {'-' * 20}")
                for e in entities:
                    value = e.get("value", "")
                    label = e.get("label", "")
                    print(f"  {value.ljust(value_width)}  | {label}")
            print()  # 엔터로 구분

if __name__ == "__main__":
    main()
