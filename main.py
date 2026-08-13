import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ================================
# 1. 환경 변수 로드
# ================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")

# 클라이언트 초기화
try:
    client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception as init_err:
    client = None
    print(f"Client init error: {init_err}")

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
        
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not GEMINI_API_KEY:
            return make_kakao_response("[오류] Render에 GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

        if not client:
            return make_kakao_response("[오류] Gemini Client 초기화에 실패했습니다.")

     # gemini-2.0-flash 대신 최신 gemini-2.5-flash 적용
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=80,
                temperature=0.5
            )
        )
        
      

        ai_reply = response.text.strip() if (response and hasattr(response, 'text') and response.text) else "답변 생성 실패"
        return make_kakao_response(ai_reply)

    except Exception as e:
        # 에러 내용을 카카오톡 메시지로 직접 출력
        return make_kakao_response(f"[API 에러 발생]: {str(e)}")

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
