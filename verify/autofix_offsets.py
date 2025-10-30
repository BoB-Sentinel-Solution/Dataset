# autofix_offsets.py
# -*- coding: utf-8 -*-

import json
import sys
import argparse
import unicodedata
import io
from typing import Dict, Tuple, Optional, List

# --- Windows stderr UTF-8 safeguard (stdout은 파일로만 씀) ---
try:
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# -------------------------------------------------------------

# 허용 라벨(사용자 제공 버전)
ALLOWED = {
    # 기본 신원 정보
    "NAME",                     # 성명
    "PHONE",                    # 전화번호
    "EMAIL",                    # Email
    "ADDRESS",                  # 주소(시·구·동/도로명·상세)
    "POSTAL_CODE",              # 우편번호
    
	# 공적 식별번호
	"PERSONAL_CUSTOMS_ID",      # 개인통관고유번호
	"RESIDENT_ID",              # 주민등록번호
    "PASSPORT",                 # 여권번호
    "DRIVER_LICENSE",           # 운전면허번호
    "FOREIGNER_ID",             # 외국인 등록번호
    "HEALTH_INSURANCE_ID",      # 건강보험증번호
    "BUSINESS_ID",              # 사업자 등록번호
    "MILITARY_ID",              # 군번
    
    # 인증 정보
    "JWT",                      # JWT (eyJ…)
    "API_KEY",                  # API 키 (Google/OpenAI/Kakao 등)
    "GITHUB_PAT",               # GitHub Personal Access Token
    "PRIVATE_KEY",              # SSH TLS/SSL PGP 개인키

    # 금융 정보
    "CARD_NUMBER",              # 카드 번호 (Luhn/모듈러스10 검증)
    "CARD_EXPIRY",              # 카드 유효 기간 (MM/YY)
    "BANK_ACCOUNT",             # 계좌번호
    "CARD_CVV",                 # CVC/CVV
    "PAYMENT_PIN",              # 통장/카드/ATM 비밀번호 (4자리 PIN)
    "MOBILE_PAYMENT_PIN",       # 모바일 결제 비밀번호 (6자리 PIN)

    # 가상화폐 정보
    "MNEMONIC",                 # 복구 시드/니모닉
    "CRYPTO_PRIVATE_KEY",       # (가상자산) 개인 키
    "HD_WALLET",                # HD 지갑 확장키 
	"PAYMENT_URI_QR",           # 결제 URI/QR (BTC, ETH, XRP, SOLANA, TRON)
		
    # 네트워크 정보 / 기타
    "IPV4",                     # ip v4
    "IPV6",                     # ip v6
    "MAC_ADDRESS",              # mac 주소
    "IMEI",                     # IMEI
}

def normalize_for_compare(s: str, use_nfkc: bool, use_casefold: bool) -> str:
    """비교용 정규화: NFC/NFKC + (옵션) casefold."""
    if s is None:
        return ""
    t = unicodedata.normalize("NFKC" if use_nfkc else "NFC", s)
    if use_casefold:
        t = t.casefold()
    return t

def find_all_exact(text: str, value: str) -> List[int]:
    """text에서 value가 정확 일치하는 시작 인덱스 목록."""
    out = []
    start = 0
    while True:
        i = text.find(value, start)
        if i == -1:
            break
        out.append(i)
        start = i + 1
    return out

def best_occurrence(candidates: List[int], prefer_begin: int) -> Optional[int]:
    """여러 후보 중 기존 begin에 가장 가까운 시작 인덱스 선택."""
    if not candidates:
        return None
    ref = prefer_begin if isinstance(prefer_begin, int) else 0
    return min(candidates, key=lambda b: abs(b - ref))

def window_bounds(n: int, center: int, value_len: int, radius: int = 96) -> Tuple[int,int]:
    """로컬 탐색 범위 계산."""
    c = center if isinstance(center, int) else 0
    L = max(0, c - radius)
    R = min(n, c + radius + max(1, value_len))
    if L >= R:
        return 0, n
    return L, R

def search_exact_within(text: str, value: str, L: int, R: int) -> List[int]:
    """구간 [L,R)에서 value 정확 매칭 시작 인덱스 목록."""
    out = []
    start = L
    while True:
        i = text.find(value, start, R)
        if i == -1:
            break
        out.append(i)
        start = i + 1
    return out

def brute_force_norm_match(text: str, value: str, prefer_begin: int, use_nfkc: bool, use_casefold: bool) -> Optional[Tuple[int,int]]:
    """
    정규화 기반 근사 탐색:
      - value[0]과 같은 지점을 후보 b로,
      - e는 b+1..b+len(value)+8 범위에서 확장하며
      - normalize(text[b:e]) == normalize(value) 인 첫 구간 채택.
    """
    if not value:
        return None
    nvalue = normalize_for_compare(value, use_nfkc, use_casefold)
    n = len(text)
    max_extra = 8
    b_hits = []

    first = value[0]
    candidate_bs = []
    pos = -1
    while True:
        pos = text.find(first, pos + 1)
        if pos == -1:
            break
        candidate_bs.append(pos)

    for b in candidate_bs:
        min_e = b + 1
        max_e = min(n, b + max(len(value),1) + max_extra)
        for e in range(min_e, max_e + 1):
            if e - b < max(1, len(value) - max_extra):
                continue
            slice_norm = normalize_for_compare(text[b:e], use_nfkc, use_casefold)
            if slice_norm == nvalue:
                b_hits.append((b, e))
                break

    if not b_hits:
        return None
    ref = prefer_begin if isinstance(prefer_begin, int) else 0
    b, e = min(b_hits, key=lambda t: (abs(t[0] - ref), (t[1]-t[0])))
    return b, e

def fix_entity_offsets(text: str, entity: dict, use_nfkc: bool, use_casefold: bool) -> Optional[Tuple[int,int]]:
    """
    엔티티 (begin,end) 자동 보정:
      1) 로컬 윈도우 정확매칭
      2) 전역 정확매칭
      3) 정규화 기반 근사 탐색
    """
    value = entity.get("value")
    b_old = entity.get("begin")
    e_old = entity.get("end")
    if not isinstance(value, str):
        return None

    n = len(text)
    vlen = len(value)

    # 1) 로컬 정확 매칭
    L, R = window_bounds(n, b_old, vlen, radius=96)
    locals_ = search_exact_within(text, value, L, R)
    if locals_:
        b_new = best_occurrence(locals_, b_old)
        if b_new is not None:
            return (b_new, b_new + vlen)

    # 2) 전역 정확 매칭
    exacts = find_all_exact(text, value)
    if exacts:
        b_new = best_occurrence(exacts, b_old)
        if b_new is not None:
            return (b_new, b_new + vlen)

    # 3) 정규화 기반 근사 탐색
    bf = brute_force_norm_match(text, value, b_old, use_nfkc, use_casefold)
    if bf:
        return bf

    return None

def apply_label_mapping(label: str, label_map: Dict[str,str]) -> str:
    """라벨 매핑 적용."""
    if not isinstance(label, str):
        return label
    return label_map.get(label, label)

def sanitize_entities(ans: dict, drop_unknown: bool, label_map: Dict[str,str],
                      use_nfkc: bool, use_casefold: bool, stats: dict):
    """
    - 오프셋 보정
    - 라벨 매핑/필터링
    - 중복 제거, begin 기준 정렬
    - has_sensitive 일관성 보정
    """
    text = ans.get("text")
    ents = ans.get("entities")
    if not isinstance(text, str) or not isinstance(ents, list):
        return

    new_ents = []
    seen = set()  # (label, begin, end)

    for ent in ents:
        if not isinstance(ent, dict):
            continue

        # 1) 라벨 변환
        lab = ent.get("label")
        lab2 = apply_label_mapping(lab, label_map) if label_map else lab

        # 2) 허용 라벨 체크
        if lab2 not in ALLOWED:
            if drop_unknown:
                stats["dropped_label"] += 1
                continue
            else:
                stats["unknown_label"] += 1  # 남겨두지만 검증기에서 경고될 수 있음

        # 3) 오프셋 정합/보정
        b = ent.get("begin")
        e = ent.get("end")
        v = ent.get("value")

        ok = (isinstance(b, int) and isinstance(e, int) and isinstance(v, str)
              and 0 <= b < e <= len(text) and text[b:e] == v)
        if not ok:
            fixed = fix_entity_offsets(text, ent, use_nfkc, use_casefold)
            if fixed:
                b2, e2 = fixed
                if normalize_for_compare(text[b2:e2], use_nfkc, use_casefold) == normalize_for_compare(v, use_nfkc, use_casefold):
                    b, e = b2, e2
                    stats["fixed_offsets"] += 1
                else:
                    stats["unmatched_offsets"] += 1
                    # 품질 위해 오프셋 못 맞춘 엔티티는 버림
                    continue

        tup = (lab2, b, e)
        if tup in seen:
            stats["dedup"] += 1
            continue
        seen.add(tup)

        ent["label"] = lab2
        ent["begin"] = b
        ent["end"] = e
        new_ents.append(ent)

    # begin 기준 정렬
    new_ents.sort(key=lambda x: (x.get("begin", 0), x.get("end", 0), x.get("label","")))
    ans["entities"] = new_ents

    # has_sensitive 보정
    hs = bool(new_ents)
    if ans.get("has_sensitive") is not hs:
        ans["has_sensitive"] = hs
        stats["fixed_has_sensitive"] += 1

def open_text_auto(path: str):
    """BOM 감지로 텍스트 모드 오픈(스트리밍). 실패 시 CP949 폴백."""
    with open(path, "rb") as fb:
        head = fb.read(4)
    if head.startswith(b'\xef\xbb\xbf'):
        enc = 'utf-8-sig'
    elif head.startswith(b'\xff\xfe'):
        enc = 'utf-16'      # LE
    elif head.startswith(b'\xfe\xff'):
        enc = 'utf-16-be'   # BE
    else:
        enc = 'utf-8'
    try:
        return open(path, "r", encoding=enc, newline=None)
    except UnicodeError:
        return open(path, "r", encoding="cp949", errors="replace", newline=None)

def process_row(row: dict, args, stats: dict) -> dict:
    msgs = row.get("messages")
    if not isinstance(msgs, list) or len(msgs) != 3:
        return row

    ac = msgs[2].get("content", "")
    try:
        ans = json.loads(ac)
    except Exception:
        return row

    if not isinstance(ans, dict):
        return row

    sanitize_entities(
        ans,
        drop_unknown=args.drop_unknown_labels,
        label_map=(args._label_map or {}),
        use_nfkc=args.nfkc,
        use_casefold=args.casefold,
        stats=stats
    )

    msgs[2]["content"] = json.dumps(ans, ensure_ascii=False)
    return row

def main():
    ap = argparse.ArgumentParser(
        description="Fix entity offsets and optionally map/drop labels; output is always UTF-8."
    )
    ap.add_argument("input", help="입력 JSONL (messages: system,user,assistant)")
    ap.add_argument("output", help="출력 JSONL (항상 UTF-8 저장)")
    ap.add_argument("--nfkc", action="store_true", help="정규화 비교 시 NFKC 사용(기본 NFC)")
    ap.add_argument("--casefold", action="store_true", help="대소문자 무시(casefold) 비교 사용")
    ap.add_argument("--label-map", type=str, default=None, help="라벨 매핑 JSON 파일 경로")
    ap.add_argument("--drop-unknown-labels", action="store_true", help="허용 라벨로 매핑되지 않으면 엔티티 삭제")
    args = ap.parse_args()

    # 라벨 매핑 로드
    args._label_map = None
    if args.label_map:
        try:
            with open(args.label_map, "r", encoding="utf-8") as fm:
                mp = json.load(fm)
                if not isinstance(mp, dict):
                    raise ValueError("label_map must be a JSON object")
                args._label_map = mp
        except Exception as e:
            sys.stderr.write(f"[autofix] label-map load failed: {e}\n")
            args._label_map = None

    stats = {
        "lines": 0,
        "fixed_offsets": 0,
        "unmatched_offsets": 0,
        "dropped_label": 0,
        "unknown_label": 0,
        "dedup": 0,
        "fixed_has_sensitive": 0,
    }

    with open_text_auto(args.input) as fin, open(args.output, "w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            raw = line.rstrip("\n")
            if not raw.strip():
                fout.write(raw + "\n")
                continue
            stats["lines"] += 1
            try:
                row = json.loads(raw)
            except Exception:
                # JSON 깨진 줄은 그대로 통과
                fout.write(raw + "\n")
                continue

            row2 = process_row(row, args, stats)
            fout.write(json.dumps(row2, ensure_ascii=False) + "\n")

    sys.stderr.write(
        "[autofix] lines={lines} fixed_offsets={fixed_offsets} unmatched_offsets={unmatched_offsets} "
        "dropped_label={dropped_label} unknown_label={unknown_label} dedup={dedup} "
        "fixed_has_sensitive={fixed_has_sensitive}\n".format(**stats)
    )

if __name__ == "__main__":
    main()
