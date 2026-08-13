import os
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ================================
# 1. 환경 변수 및 Client 로드
# ================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)

# ================================
# 2. 산행 대장 페르소나 (시스템 프롬프트)
# ================================
SYSTEM_PROMPT = (
    "너는 아틀란타 KAL 하이킹팀의 '산행 대장'이다. "
    "회원들의 질문에 대해 50대 산행 대장의 친절하고 든든한 어조(~입니다, ~하세요)로 딱 1문장으로만 대답해라. "
    "영어나 태그, 이상한 기호는 절대 출력하지 마라."
)

# ================================
# 3. 라우트 및 카카오 스킬
# ================================

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json(silent=True) or {}
        
        # 카카오톡 입력 발화문 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = req_data.get('action', {}).get('params', {}).get('sys_text', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("산행 대장입니다! (API 키가 설정되지 않았습니다.)")

        # Gemini API 호출 (속도 최적화: gemini-2.5-flash / gemini-1.5-flash 사용)
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=50,
                    temperature=0.2
                )
            )
        except Exception as api_err:
            print(f"Primary model error: {api_err}")
            # 백업 모델 호출
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=50,
                    temperature=0.2
                )
            )

        ai_reply = ""
        if response and hasattr(response, 'text') and response.text:
            ai_reply = response.text.strip()

        # 영문/태그 제거 정제
        ai_reply = re.sub(r'/[A-Za-z0-9_:]+.*', '', ai_reply).strip()

        if not ai_reply:
            ai_reply = "반갑습니다! KAL 하이킹팀 산행 대장입니다. 무엇이 궁금하신가요?"

        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Total Kakao Skill Error: {e}")
        return make_kakao_response("반갑습니다! 아틀란타 KAL 하이킹 산행 대장입니다. 편하게 질문해 주세요.")

# 카카오톡 응답 규격 JSON 포맷
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
