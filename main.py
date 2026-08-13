import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

# ================================
# 1. 환경 변수 로드
# ================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)

# ================================
# 2. 시스템 프롬프트
# ================================
SYSTEM_PROMPT = (
    "너는 아틀란타 KAL 하이킹팀의 Hiking 대장이야. "
    "회원들의 질문에 대해 핵심만 1~2문장으로 아주 짧고 친절하게 한국어로 답변해줘."
)

# ================================
# 3. 기본 라우트
# ================================
@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

# ================================
# 4. Kakao Skill 엔드포인트
# ================================
@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json() or {}

        # 카카오톡 입력 메시지
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("Gemini API 키가 설정되지 않았습니다.")

        # ================================
        # 🔥 interactions.create() 최적화 (SDK 완전 호환)
        # ================================
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            system_instruction=SYSTEM_PROMPT,
            input=user_message,
            extra_body={
                "response_modalities": ["text"],
                "generation_config": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "max_output_tokens": 60
                    # candidate_count 제거 (SDK가 지원 안 함)
                }
            }
        )

        # ================================
        # 🔥 안전 파싱
        # ================================
        ai_reply = ""

        try:
            if hasattr(interaction, "output_text") and interaction.output_text:
                ai_reply = interaction.output_text.strip()

            elif hasattr(interaction, "candidates") and interaction.candidates:
                parts = interaction.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    ai_reply = parts[0].text.strip()

            else:
                ai_reply = "답변을 생성하지 못했습니다."

        except Exception as parse_error:
            print("Parsing Error:", parse_error)
            ai_reply = "답변 생성 중 오류가 발생했습니다."

        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"[Gemini Error] {e}")
        return make_kakao_response("하이킹 대장 로봇입니다. 잠시 후 다시 시도해주세요.")

# ================================
# 5. Kakao 응답 포맷
# ================================
def make_kakao_response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    })

# ================================
# 6. 실행
# ================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
