import os
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ================================
# 1. 환경 변수 로드
# ================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)

# ================================
# 2. 아주 간결한 시스템 프롬프트 (속도 최적화)
# ================================
SYSTEM_PROMPT = (
    "너는 아틀란타 KAL 하이킹팀의 '산행 대장'이다. "
    "반드시 50대 산행 대장 어조(~입니다, ~세요)로 딱 한 문장으로만 아주 짧게 한국어로 대답해라. "
    "영어나 시스템 제어 태그는 절대 쓰지 마라."
)

# ================================
# 3. 라우트 및 카카오 스킬 설정
# ================================

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json(silent=True) or {}
        
        # 메시지 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = req_data.get('action', {}).get('params', {}).get('sys_text', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("GEMINI API 키가 설정되지 않았습니다.")

        # Gemini API 호출 (응답 속도 최적화: max_tokens=60으로 제한)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=60,
                temperature=0.3
            )
        )

        ai_reply = ""
        if response and hasattr(response, 'text') and response.text:
            ai_reply = response.text.strip()

        # 시스템 태그 제거
        ai_reply = re.sub(r'/[A-Za-z0-9_:]+.*', '', ai_reply).strip()

        if not ai_reply:
            ai_reply = "반갑습니다! KAL 하이킹팀 산행 대장입니다. 무슨 문의이신가요?"

        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return make_kakao_response("반갑습니다! 아틀란타 KAL 하이킹 산행 대장입니다. 무엇을 도와드릴까요?")

# 카카오톡 응답 포맷
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
# 4. 실행
# ================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
