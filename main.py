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
# 3. 라우트 및 카카오 스킬 설정
# ================================

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json(silent=True) or {}
        
        # 카카오톡 발화문(utterance) 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            # fallback/bot block 기본 발화 예외 처리
            user_message = req_data.get('action', {}).get('params', {}).get('sys_text', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("[오류] GEMINI API 키가 설정되지 않았습니다.")

        # Gemini API 호출
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=150,
                temperature=0.5
            )
        )

        # Gemini 응답 텍스트 파싱
        ai_reply = ""
        if response:
            try:
                if hasattr(response, 'text') and response.text:
                    ai_reply = response.text.strip()
                elif hasattr(response, 'candidates') and response.candidates:
                    parts = response.candidates[0].content.parts
                    ai_reply = "".join([p.text for p in parts if hasattr(p, 'text')]).strip()
            except Exception as parse_err:
                print(f"Parsing error: {parse_err}")

        if not ai_reply:
            ai_reply = "안녕하세요! 아틀란타 KAL 하이킹 대장입니다. 무엇이 궁금하신가요?"

        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return make_kakao_response(f"[에러 발생]: {str(e)}")

# 카카오톡 i Open Builder 스킬 응답 규격 JSON
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
