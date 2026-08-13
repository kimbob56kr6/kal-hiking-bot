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
# 2. 강력하게 고정된 시스템 프롬프트 (캐릭터/페르소나)
# ================================
SYSTEM_PROMPT = (
    "너의 이름은 '산행 대장'이며, 아틀란타 KAL 하이킹팀의 대장이다. "
    "다음 규칙을 철저히 지켜라:\n"
    "1. 항상 회원들을 아끼고 산을 사랑하는 든든하고 친절한 50대 산행 대장의 말투(~입니다, ~하세요, ~죠!)를 사용해라.\n"
    "2. 영어나 '/Tone:', '/Ask' 같은 시스템 제어 태그, 특수 기호 조합만 있는 답변은 절대로 출력하지 마라.\n"
    "3. 모든 질문에 대해 1~2문장의 자연스러운 한국어 완성형 문장으로만 답변해라."
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
            return make_kakao_response("[오류] GEMINI API 키가 설정되지 않았습니다.")

        # Gemini API 호출
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=150,
                temperature=0.4
            )
        )

        ai_reply = ""
        if response and hasattr(response, 'text') and response.text:
            ai_reply = response.text.strip()

        # 영문 메타태그(/Tone:, /Ask 등)가 섞여 나온 경우 찌꺼기 제거
        ai_reply = re.sub(r'/[A-Za-z0-9_:]+.*', '', ai_reply).strip()

        if not ai_reply:
            ai_reply = "안녕하세요! 아틀란타 KAL 하이킹 산행 대장입니다. 무엇이 궁금하신가요?"

        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return make_kakao_response("아틀란타 KAL 하이킹 대장 로봇입니다. 잠시 후 다시 질문해 주세요.")

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
