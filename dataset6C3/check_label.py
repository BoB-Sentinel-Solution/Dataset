#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json

SEP = "─" * 60

def parse_line(line: str):
    """한 줄 JSON을 파싱하고 통일된 dict로 반환
    반환 값: {id, text, has_sensitive, entities(list[dict])}
    """
    obj = json.loads(line)

    # 기본값
    rec = {
        "id": obj.get("id"),
        "text": obj.get("text"),
        "has_sensitive": obj.get("has_sensitive"),
        "entities": obj.get("entities", []),
    }

    # answer 키가 있으면 내부 JSON(문자열 or dict)에서 다시 추출
    if "answer" in obj:
        ans = obj["answer"]
        if isinstance(ans, str):
            try:
                ans = json.loads(ans)
            except json.JSONDecodeError:
                # answer가 문자열이지만 JSON이 아니면 무시
                ans = {}
        if isinstance(ans, dict):
            # 바깥 값보다 answer 내부 값을 우선
            rec["text"] = ans.get("text", rec["text"])
            rec["has_sensitive"] = ans.get("has_sensitive", rec["has_sensitive"])
            rec["entities"] = ans.get("entities", rec["entities"])

    # 엔티티가 None이면 빈 리스트로
    if rec["entities"] is None:
        rec["entities"] = []

    return rec


def left(s, n):
    return s[:max(n, 0)] if s else ""

def right(s, n):
    return s[-max(n, 0):] if s else ""

def context_around(text, begin, end, pad=12):
    """begin/end 기준으로 좌우 컨텍스트 생성 (텍스트 없거나 위치가 없으면 '')"""
    if text is None:
        return ""
    try:
        b = int(begin)
        e = int(end)
    except (TypeError, ValueError):
        return ""
    b = max(0, min(b, len(text)))
    e = max(0, min(e, len(text)))
    pre = text[max(0, b - pad):b]
    mid = text[b:e]
    post = text[e:min(len(text), e + pad)]
    # 시각 강조용 꺽쇠
    return f"{pre}⟦{mid}⟧{post}"


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

            rec = parse_line(line)
            _id = rec.get("id")
            text = rec.get("text")
            has_sensitive = rec.get("has_sensitive")
            entities = rec.get("entities", [])

            # 컬럼 폭 계산
            value_width = max([len(e.get("value", "")) for e in entities] + [5])
            label_width = max([len(e.get("label", "")) for e in entities] + [5])
            span_width = max([len(f"{e.get('begin','')}-{e.get('end','')}") for e in entities] + [9])
            idx_width = len(str(len(entities))) if entities else 1

            # 헤더
            print(SEP)
            print(f"ID: { _id } | has_sensitive: {has_sensitive}")
            if text:
                # 텍스트는 너무 길 수 있어 처음 120자만 간략 표시
                preview = text.replace("\n", " ")
                if len(preview) > 120:
                    preview = preview[:120] + "…"
                print(f"TEXT: {preview}")

            print(SEP)
            if not entities:
                print("  (entities 없음)\n")
                continue

            # 표 헤더
            header = (
                f"  {'#'.ljust(idx_width)}  "
                f"{'VALUE'.ljust(value_width)}  | "
                f"{'LABEL'.ljust(label_width)}  | "
                f"{'SPAN'.ljust(span_width)}"
            )
            print(header)
            print(
                f"  {'-'*idx_width}  "
                f"{'-'*value_width}  | "
                f"{'-'*label_width}  | "
                f"{'-'*span_width}"
            )

            # 표 본문
            for i, e in enumerate(entities, start=1):
                value = e.get("value", "")
                label = e.get("label", "")
                begin = e.get("begin", "")
                end = e.get("end", "")
                span = f"{begin}-{end}"

                print(
                    f"  {str(i).ljust(idx_width)}  "
                    f"{value.ljust(value_width)}  | "
                    f"{label.ljust(label_width)}  | "
                    f"{span.ljust(span_width)}"
                )

                # 컨텍스트 한 줄 추가(가능할 때만)
                ctx = context_around(text, begin, end, pad=12)
                if ctx:
                    print(f"     ↳ {ctx}")

            print()  # 엔터로 구분

if __name__ == "__main__":
    main()