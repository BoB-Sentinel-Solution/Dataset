import json, sys

IN  = sys.argv[1] if len(sys.argv) > 1 else "in.jsonl"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out.jsonl"

OFFSET = 1610         # id_new = id_old + 1610  →  1→1611, 325→1935
LOW, HIGH = 1, 325    # 기대하는 기존 id 범위

bad = 0
n = 0

with open(IN, "r", encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as w:
    for ln, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        old = obj.get("id")
        if not isinstance(old, int):
            print(f"[L{ln}] WARN: id가 정수가 아닙니다: {old!r}", file=sys.stderr)
            bad += 1
        if isinstance(old, int) and (LOW <= old <= HIGH):
            obj["id"] = old + OFFSET
        elif isinstance(old, int):
            # 범위 밖 id도 그대로 offset 적용하고 싶다면 위 조건을 삭제하세요.
            print(f"[L{ln}] WARN: id {old}가 예상 범위({LOW}~{HIGH}) 밖입니다. 변경하지 않음.", file=sys.stderr)
        w.write(json.dumps(obj, ensure_ascii=False) + "\n")
        n += 1

print(f"done. wrote {n} lines to {OUT}. warnings={bad}", file=sys.stderr)
