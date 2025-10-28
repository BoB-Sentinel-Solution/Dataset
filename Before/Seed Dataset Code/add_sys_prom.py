import json

# 파일 경로 직접 지정
input_file = "1.jsonl"
output_file = "2.jsonl"

# 공통 system 프롬프트
system_prompt = (
    "You are a strict detector for sensitive entities (PII and secrets).\n"
    "Given the user's text, return ONLY a JSON with keys\n"
    "You must output text in JSON format.\n"
    "Input : You receive an arbitrary text\n"
    "Output : \n"
    "{\n"
    "  \"text\": \"<original input text verbatim>\",\n"
    "  \"has_sensitive\": <boolean>,\n"
    "  \"entities\": [\n"
    "    {\n"
    "      \"value\": \"<exact substring as it appears>\",\n"
    "      \"begin\": <integer>,   // 0-based char offset (inclusive)\n"
    "      \"end\": <integer>,     // 0-based char offset (exclusive)\n"
    "      \"label\": \"<UPPER_SNAKE_CASE category>\"\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "Example:\n"
    "Input text:\n"
    "{\"로그인 계정명: hong_gildong, 패스워드: Abc1234! 입력 시 실패 원인을 분석해줘.\" }\n"
    "Expected output (offsets must match the exact input you receive):\n"
    "{\n"
    "  \"text\": \"로그인 계정명: hong_gildong, 패스워드: Abc1234! 입력 시 실패 원인을 분석해줘.\",\n"
    "  \"has_sensitive\": true,\n"
    "  \"entities\": [\n"
    "    { \"value\": \"hong_gildong\", \"begin\": 9, \"end\": 21, \"label\": \"USERNAME\" },\n"
    "    { \"value\": \"Abc1234!\", \"begin\": 29, \"end\": 37, \"label\": \"PASSWORD\" }\n"
    "  ]\n"
    "}\n"
    "Example 2:\n"
    "Input text:\n"
    "{\"고객 불만 사항에 대응하기 위한 표준 절차를 정리해줘.\"}\n"
    "Expected Output:\n"
    "{\n"
    "  \"text\": \"고객 불만 사항에 대응하기 위한 표준 절차를 정리해줘.\",\n"
    "  \"has_sensitive\": false,\n"
    "  \"entities\": []\n"
    "}"
)

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

updated = []
for line in lines:
    obj = json.loads(line)
    for msg in obj["messages"]:
        if msg["role"] == "system" and msg["content"].strip() == "":
            msg["content"] = system_prompt
    updated.append(obj)

with open(output_file, "w", encoding="utf-8") as f:
    for item in updated:
        f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + "\n")

print(f"✅ 완료! 모든 system content 빈 항목을 채운 새 파일 저장됨: {output_file}")
