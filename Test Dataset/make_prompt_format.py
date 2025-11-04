# build_dataset_jsonl_text_only.py
# -*- coding: utf-8 -*-
import json, csv, argparse, sys, os
from typing import Any, Dict, Iterable, Union, Optional

# ---------------- I/O ----------------
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
                    snippet = s[:120]; pointer = ""
                sys.stderr.write(
                    f"\n[JSON ERROR] {path}:{lineno} (lineno={lno}, colno={col}, pos={pos})\n"
                    f"error: {e}\ncontext: {snippet}\n         {pointer}\n"
                )
                sys.stderr.flush()
                raise SystemExit(1)

# ---------------- helpers ----------------
def parse_json_maybe(x: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    return json.loads(x)

def extract_from_messages(row: Dict[str, Any]) -> Optional[str]:
    """
    messages 배열에서 첫 user의 content를 텍스트로 사용.
    """
    msgs = row.get("messages")
    if not isinstance(msgs, list):
        return None
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "user":
            return m.get("content")
    return None

def normalize_row_to_text(row: Dict[str, Any]) -> Dict[str, Optional[Union[int,str]]]:
    """
    다양한 입력 스키마를 'id(옵션), text(필수)'로 정규화.
      허용 스키마:
        1) {"id", "text"}                            -> 그대로 사용
        2) {"id", "content", "has_sensitive", ...}   -> text = content
        3) {"id", "messages":[{"role":"user","content":...}, ...]} -> text = user.content
        4) {"id", "user": "..."}                     -> text = user
    """
    rec_id = row.get("id")
    try:
        # id가 숫자 문자열일 수도 있으니 그대로 문자열화는 나중에
        if rec_id is not None and isinstance(rec_id, str) and rec_id.strip() == "":
            rec_id = None
        if rec_id is not None and not isinstance(rec_id, (str, int)):
            rec_id = str(rec_id)
    except Exception:
        rec_id = None

    # 1) id + text
    if "text" in row and isinstance(row["text"], str):
        return {"id": rec_id, "text": row["text"]}

    # 2) content + has_sensitive + entities
    if "content" in row and isinstance(row["content"], str):
        return {"id": rec_id, "text": row["content"]}

    # 3) messages[]
    msg_text = extract_from_messages(row)
    if isinstance(msg_text, str):
        return {"id": rec_id, "text": msg_text}

    # 4) user
    if "user" in row and isinstance(row["user"], str):
        return {"id": rec_id, "text": row["user"]}

    # 5) assistant만 있고 content가 있는 경우(드문 케이스) → content를 텍스트로
    if "assistant" in row and isinstance(row["assistant"], dict) and "content" in row["assistant"]:
        if "content" in row:
            return {"id": rec_id, "text": row["content"]}

    raise RuntimeError("Unrecognized input schema for row (no text found).")

def build_records(rows: Iterable[Dict[str, Any]], start_id: Optional[int], force_start: bool) -> Iterable[Dict[str, str]]:
    cur_id = start_id
    for idx, row in enumerate(rows, 1):
        try:
            norm = normalize_row_to_text(row)
        except Exception as e:
            sys.stderr.write(f"\n[SCHEMA ERROR] at input row #{idx}\n")
            try:
                sys.stderr.write(f"keys: {list(row.keys())}\n")
            except Exception:
                pass
            try:
                sys.stderr.write(f"row-json: {json.dumps(row, ensure_ascii=False)}\n")
            except Exception:
                sys.stderr.write(f"row-str: {str(row)}\n")
            sys.stderr.write(f"error: {e}\n\n")
            sys.stderr.flush()
            raise

        # id 결정
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

        # 문자열 id로 출력
        yield {"id": str(rec_id), "text": norm["text"]}

def write_jsonl(records: Iterable[Dict[str, Any]], out_path: str):
    abs_out = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
    with open(abs_out, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"[OK] Wrote -> {abs_out}")

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(description="Convert various schemas to JSONL of {'id':'<str>','text':'<str>'}")
    ap.add_argument("--input", required=True, help="입력 파일 (CSV or JSONL)")
    ap.add_argument("--out", required=True, help="출력 JSONL")
    ap.add_argument("--format", choices=["csv","jsonl"], default=None, help="입력 포맷 (미지정 시 확장자로 추론)")
    ap.add_argument("--start-id", type=int, default=None, help="시작 id (입력에 id 없거나 --force-start일 때 사용)")
    ap.add_argument("--force-start", action="store_true", help="입력의 기존 id를 무시하고 --start-id부터 재부여")
    args = ap.parse_args()

    fmt = args.format or ("csv" if args.input.lower().endswith(".csv") else "jsonl")
    rows = read_csv_rows(args.input) if fmt == "csv" else read_jsonl_rows(args.input)

    write_jsonl(
        build_records(rows, start_id=args.start_id, force_start=args.force_start),
        args.out
    )

if __name__ == "__main__":
    main()
