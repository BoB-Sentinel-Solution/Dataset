#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def strip_writing_style(input_path: str, output_path: str) -> None:
    in_path = Path(input_path)
    out_path = Path(output_path)

    with in_path.open("r", encoding="utf-8") as fin, \
         out_path.open("w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue  # 빈 줄 스킵

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # 혹시 모를 깨진 줄은 그대로 넘기거나 로그 남기고 싶으면 여기에 처리
                continue

            # writing_style 키 제거
            obj.pop("writing_style", None)
            obj.pop("style", None)

            fout.write(json.dumps(obj, ensure_ascii=False))
            fout.write("\n")


if __name__ == "__main__":
    # 사용법: python strip_ws.py input.jsonl output.jsonl
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.jsonl> <output.jsonl>")
        sys.exit(1)

    strip_writing_style(sys.argv[1], sys.argv[2])
