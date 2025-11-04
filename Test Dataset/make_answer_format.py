# build_dataset_jsonl_answer_only.py
# -*- coding: utf-8 -*-
import json, csv, argparse, sys, os
from typing import Any, Dict, Iterable, Union, Optional

def read_csv_rows(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield row

def read_jsonl_rows(path: str):
    with open(path, encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, 1):
            s = line.rstrip("\r\n")
            if not s:
                continue
            try:
                yield json.loads(s)
            except json.JSONDecodeError as e:
                pos    = getattr(e, "pos", None)
                lno    = getattr(e, "lineno", lineno)
                col    = getattr(e, "colno", None)
                if pos is not None:
                    start = max(0, pos - 60)
                    end   = min(len(s), pos + 60)
                    snippet = s[start:end]
                    pointer = " " * (pos - start) + "^"
                else:
                    snippet = s[:120]
                    pointer = ""
                sys.stderr.write(
                    f"\n[JSON ERROR] {path}:{lineno} "
                    f"(lineno={lno}, colno={col}, pos={pos})\n"
                    f"error: {e}\n"
                    f"context: {snippet}\n"
                    f"         {pointer}\n"
                )
                sys.stderr.flush()
                raise SystemExit(1)
            except Exception as e:
                sys.stderr.write(
                    f"\n[READ ERROR] {path}:{lineno}\n{type(e).__name__}: {e}\n"
                    f"line(raw): {s[:120]}\n"
                )
                sys.stderr.flush()
                raise SystemExit(1)

def parse_json_maybe(x: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(x, dict): 
        return x
    return json.loads(x)

def extract_from_messages(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    msgs = row.get("messages")
    if not isinstance(msgs, list): 
        return None
    user_text = None
    assistant_payload = None
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "user":
            user_text = m.get("content"); break
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "assistant":
            assistant_payload = m.get("content"); break
    if user_text is None or assistant_payload is None: 
        return None
    assist_obj = json.loads(assistant_payload) if isinstance(assistant_payload, str) else assistant_payload
    return {"user": user_text, "assistant_json": assist_obj}

def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return: {'id': int|None, 'user': str, 'assistant_json': dict}
    허용 스키마:
      1) {'id', 'content', 'has_sensitive', 'entities'}
      2) {'id', 'messages':[{'role':'user'}, {'role':'assistant'}]}
      3) {'id', 'user', 'assistant_json'|assistant|assistant_obj}
    """
    rec_id = int(row["id"]) if "id" in row and str(row["id"]).strip() != "" else None

    if "user" in row and ("assistant_json" in row or "assistant" in row or "assistant_obj" in row):
        user_text = row["user"]
        assist_raw = row.get("assistant_json") or row.get("assistant") or row.get("assistant_obj")
        assist_obj = parse_json_maybe(assist_raw)
        return {"id": rec_id, "user": user_text, "assistant_json": assist_obj}

    if "content" in row and "has_sensitive" in row and "entities" in row:
        user_text = row["content"]
        assist_obj = {"text": row["content"], "has_sensitive": row["has_sensitive"], "entities": row["entities"]}
        return {"id": rec_id, "user": user_text, "assistant_json": assist_obj}

    from_msgs = extract_from_messages(row)
    if from_msgs is not None:
        return {"id": rec_id, **from_msgs}

    if "assistant" in row and isinstance(row["assistant"], dict) and "content" in row:
        return {"id": rec_id, "user": row["content"], "assistant_json": row["assistant"]}

    raise RuntimeError("Unrecognized input schema for row.")

def build_from_rows(rows: Iterable[Dict[str, Any]], start_id: Optional[int], force_start: bool) -> Iterable[Dict[str, Any]]:
    cur_id = start_id
    for idx, row in enumerate(rows, 1):
        try:
            norm = normalize_row(row)
        except Exception as e:
            sys.stderr.write("\n[SCHEMA ERROR] at input row #{idx}\n".format(idx=idx))
            try:
                sys.stderr.write("keys: {keys}\n".format(keys=list(row.keys())))
            except Exception:
                pass
            try:
                sys.stderr.write("row-json: {j}\n".format(j=json.dumps(row, ensure_ascii=False)))
            except Exception:
                sys.stderr.write("row-str: {s}\n".format(s=str(row)))
            sys.stderr.write("error: {e}\n\n".format(e=e))
            sys.stderr.flush()
            raise

        if force_start:
            if cur_id is None:
                raise RuntimeError("--force-start requires --start-id")
            rec_id, cur_id = cur_id, cur_id + 1
        else:
            rec_id = norm["id"]
            if rec_id is None:
                if cur_id is None:
                    raise RuntimeError("Provide --start-id or include 'id' in input rows")
                rec_id, cur_id = cur_id, cur_id + 1

        # 출력 스펙: {"id":"<str>", "answer":"<assistant JSON as string>"}
        answer_str = json.dumps(norm["assistant_json"], ensure_ascii=False, separators=(",",":"))
        yield {"id": str(rec_id), "answer": answer_str}

def write_jsonl(records: Iterable[Dict[str, Any]], out_path: str):
    abs_out = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
    with open(abs_out, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",",":")) + "\n")
    print(f"[OK] Wrote -> {abs_out}")

def main():
    ap = argparse.ArgumentParser(description="Convert to {'id': '<str>', 'answer': '<assistant-json-string>'} JSONL")
    ap.add_argument("--input", required=True, help="입력 파일 (CSV or JSONL)")
    ap.add_argument("--out", required=True, help="출력 JSONL")
    ap.add_argument("--format", choices=["csv","jsonl"], default=None, help="입력 포맷 (미지정 시 확장자로 추론)")
    ap.add_argument("--start-id", type=int, default=None, help="시작 id (입력에 id 없거나 --force-start일 때 사용)")
    ap.add_argument("--force-start", action="store_true", help="입력의 기존 id를 무시하고 --start-id부터 재부여")
    args = ap.parse_args()

    fmt = args.format or ("csv" if args.input.lower().endswith(".csv") else "jsonl")
    rows = read_csv_rows(args.input) if fmt == "csv" else read_jsonl_rows(args.input)

    write_jsonl(
        build_from_rows(rows, start_id=args.start_id, force_start=args.force_start),
        args.out
    )

if __name__ == "__main__":
    main()
