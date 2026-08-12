import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ================================
# 1. 환경 변수 로드
# ================================
load_dotenv()

# Gemini SDK 표준 환경 변수명 사용
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
if not GEMINI_API_KEY:
    print("오류: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    exit(1)

# ================================
# 2. Gemini 클라이언트 초기화
# ================================
client = genai.Client(api_key=GEMINI_API_KEY)

# ================================
# 3. 시스템 프롬프트 설정
# ================================
SYSTEM_PROMPT = (
    "너는 애틀랜타 KAL 등산회의 AI Hiking 대장이야. "
    "질문에 대해 가장 핵심적인 내용을 1~2문장으로 아주 짧고 친절하게 한국어로 답변해줘."
)

# ================================
# 4. 대화 테스트 함수
# ================================
def test_chat():
    print("=== KAL 등산회 AI 대장 로컬 테스트 시작 ===")
    print("종료하려면 'exit' 또는 'quit'을 입력하세요.\n")

    while True:
        user_input = input("사용자: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit']:
            print("테스트를 종료합니다.")
            break

        try:
            # 최신 SDK 올바른 호출 방식
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=150
                )
            )

            print(f"AI 대장: {response.text.strip()}\n")

        except Exception as e:
            print("오류 발생:", e)

# ================================
# 5. 실행 시작
# ================================
if __name__ == "__main__":
    test_chat()
