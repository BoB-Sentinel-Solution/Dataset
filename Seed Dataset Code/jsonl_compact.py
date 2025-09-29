import json

# 👉 직접 경로 지정
input_file = "./id1-id320.jsonl"          # 원본 JSONL 파일 경로
output_file = "./id1-id320_compact.jsonl" # 결과 저장할 파일 경로

flattened = []

with open(input_file, "r", encoding="utf-8") as f:
    buffer = ""
    for line in f:
        buffer += line.strip()
        # JSON 객체의 끝 패턴 감지 (}]})
        if line.strip().endswith("}]}"):
            try:
                obj = json.loads(buffer)
                flattened.append(obj)
            except Exception as e:
                print("JSON parsing error:", e)
            buffer = ""

# compact JSONL로 저장 (띄어쓰기 없음)
with open(output_file, "w", encoding="utf-8") as f:
    for item in flattened:
        f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + "\n")

print(f"✅ 변환 완료! 결과 파일: {output_file}")
