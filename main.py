import os
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

# ================================
# 1. 환경 변수 로드
# ================================
load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GENAI_API_KEY) if GENAI_API_KEY else None

app = Flask(__name__)

# ================================
# 2. 시스템 프롬프트 (VS Code와 동일)
# ================================
SYSTEM_PROMPT = (
    "너는 애틀란타 KAL 하이킹팀의 Hiking 대장이야. "
    "회원들 문의에 대해 가장 핵심적인 내용을 1~2 문장으로 아주 짧고 친절하게 한국어로 답변해 줘."
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
        
        # 카카오톡 발화문 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = req_data.get('action', {}).get('params', {}).get('sys_text', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("[오류] GENAI_API_KEY가 설정되지 않았습니다.")

        # VS Code에서 성공한 바로 그 방식 그대로 호출
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=[
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                {"role": "user", "parts": [{"text": user_message}]}
            ]
        )

        ai_reply = ""
        if response and hasattr(response, 'text') and response.text:
            ai_reply = response.text.strip()

        # 영문 제어 태그 정제
        ai_reply = re.sub(r'/[A-Za-z0-9_:]+.*', '', ai_reply).strip()

        if not ai_reply:
            ai_reply = "반갑습니다! KAL 하이킹팀 산행 대장입니다. 무엇이 궁금하신가요?"

        return make_kakao_response(ai_reply)

    except Exception as e:
        error_msg = f"[API 에러 원인]: {str(e)}"
        print(f"Total Kakao Skill Error: {e}")
        return make_kakao_response(error_msg)

# 카카오톡 응답 JSON 포맷
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
# 4. 서버 실행
# ================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
