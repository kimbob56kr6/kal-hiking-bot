import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

# ================================
# 1. 환경 변수 로드 (.env 및 서버 환경변수 대응)
# ================================
load_dotenv()

# 표준 GEMINI_API_KEY 또는 GENAI_API_KEY 모두 지원
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")

# 클라이언트 초기화
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)

# ================================
# 2. 시스템 프롬프트 설정
# ================================
SYSTEM_PROMPT = (
    "너는 아틀란타 KAL 하이킹팀의 Hiking 대장이야. "
    "회원들 문의에 대해 가장 핵심적인 내용을 1~2문장으로 아주 짧고 친절하게 한국어로 답변해줘."
)

# ================================
# 3. 라우트 설정
# ================================

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json() or {}
        
        # 카카오톡 입력 메시지 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("GEMINI API 키 설정이 안 되어 있습니다.")

        # Interactions API 올바른 호출 방식 (input 텍스트로 프롬프트 전달)
        prompt = f"System: {SYSTEM_PROMPT}\nUser: {user_message}"
        
        interaction = client.interactions.create(
            model='gemini-2.5-flash',
            input=prompt
        )

        ai_reply = interaction.outputs[-1].text.strip() if interaction.outputs else "답변을 생성하지 못했습니다."
        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return make_kakao_response("아틀란타 KAL 하이킹 대장 로봇입니다. 잠시 후 다시 질문해 주세요.")

# 카카오톡 응답 규격 포맷 함수
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
# 4. 실행 시작
# ================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
