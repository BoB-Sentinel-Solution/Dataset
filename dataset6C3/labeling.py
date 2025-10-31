#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import sys
import argparse

# -------------------------
# 패턴 정의
# -------------------------

# JWT: header.payload.signature ('.' 정확히 2개)
JWT_RE = re.compile(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')

# IPv4
IPV4_RE = re.compile(
    r'^(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)'
    r'(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$'
)

# 아주 기본적인 IPv6 (필요시 확장)
IPV6_RE = re.compile(r'^[0-9A-Fa-f:]+(?:%.+)?(?:/\d+)?$')

# MAC (콜론/대시) + 12hex
MAC_RE = re.compile(
    r'^([0-9A-Fa-f]{2}[:\-]){5}([0-9A-Fa-f]{2})$|^[0-9A-Fa-f]{12}$'
)

# GitHub PAT
GITHUB_PAT_RE = re.compile(r'^(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{10,}$')

# API KEY (예시)
API_KEY_RE = re.compile(
    r'^(sk-[A-Za-z0-9\-]{8,}|sk-elastic-[A-Za-z0-9\-]{4,})$'
)

def looks_like_private_key(value: str) -> bool:
    v = value.strip()
    return v.startswith("-----BEGIN ") and "PRIVATE KEY-----" in v

def guess_label(value: str) -> str:
    # 순서는 중요함: 더 구체적인 것부터
    if JWT_RE.match(value):
        return "JWT"

    if IPV4_RE.match(value):
        return "IPV4"

    if IPV6_RE.match(value) and ":" in value:
        return "IPV6"

    if MAC_RE.match(value):
        return "MAC_ADDRESS"

    # 여기서부터 Luhn 안 씀: 15자리 숫자면 IMEI로 간주
    if re.fullmatch(r'\d{15}', value):
        return "IMEI"

    if GITHUB_PAT_RE.match(value):
        return "GITHUB_PAT"

    if API_KEY_RE.match(value):
        return "API_KEY"

    if looks_like_private_key(value):
        return "PRIVATE_KEY"

    return "UNKNOWN"  # 필요 없으면 None 리턴으로 바꿔도 됨

def process_line(line: str) -> str:
    obj = json.loads(line)

    entities = obj.get("entities", [])
    for ent in entities:
        # 이미 label 있으면 건너뜀
        if "label" in ent and ent["label"]:
            continue
        value = ent.get("value", "")
        label = guess_label(value)
        if label:
            ent["label"] = label

    obj["entities"] = entities
    return json.dumps(obj, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Add label to entities based on value")
    parser.add_argument("--input", "-i", type=str, default="-", help="input JSONL (default: stdin)")
    parser.add_argument("--output", "-o", type=str, default="-", help="output JSONL (default: stdout)")
    args = parser.parse_args()

    fin = sys.stdin if args.input == "-" else open(args.input, "r", encoding="utf-8")
    fout = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")

    with fin, fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            out_line = process_line(line)
            fout.write(out_line + "\n")

if __name__ == "__main__":
    main()
