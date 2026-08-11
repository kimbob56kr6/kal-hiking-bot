import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Gemini API 클라이언트 초기화
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# AI 로봇 시스템 프롬프트
SYSTEM_PROMPT = """
너는 '애틀랜타 KAL 등산회'의 AI 등산 대장이야.
질문에 대해 가장 핵심적인 내용을 딱 1~2문장으로 한국어로 아주 짧고 빠르게 답변해줘.
"""

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot (Gemini Version) is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json() or {}
        
        # 카카오톡 발화문 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("GEMINI API 키 설정 확인이 필요합니다.")

        # Gemini 2.5 Flash 모델 호출 및 속도 최적화 설정
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=150,  # 타임아웃 방지를 위한 짧은 답변 제한
                temperature=0.5,
            ),
        )

        ai_reply = response.text.strip()
        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Error handling request: {e}")
        return make_kakao_response("KAL 등산회 대장 로봇입니다. 잠시 후 다시 질문해 주세요.")

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
