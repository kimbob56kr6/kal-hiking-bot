import os
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Gemini API 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = "너는 '애틀랜타 KAL 등산회'의 AI Hiking 대장이야. 질문에 대해 가장 핵심적인 내용을 1~2문장으로 아주 짧고 친절하게 한국어로 답변해줘."

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot (Gemini 1.5 Flash Version) is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json() or {}
        
        # 카카오톡 메시지 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not GEMINI_API_KEY:
            return make_kakao_response("GEMINI API 키 설정 확인이 필요합니다.")

        # Gemini 1.5 Flash 모델 사용
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )

        response = model.generate_content(user_message)
        ai_reply = response.text.strip()
        
        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return make_kakao_response("아틀란타 KAL 하이킹 대장 로봇입니다. 잠시 후 다시 질문해 주세요.")

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
