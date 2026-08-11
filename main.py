import os
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Groq 클라이언트 초기화
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# AI 로봇 시스템 프롬프트 (속도 최적화를 위해 매우 간결하고 명확한 지침 설정)
SYSTEM_PROMPT = """
너는 '애틀랜타 KAL 등산회'의 AI 등산 대장이야.
질문에 대해 가장 핵심적인 내용을 딱 1~2문장으로 한국어로 아주 짧고 빠르게 답변해줘.
"""

@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json() or {}
        
        # 사용자의 발화 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        # API 키가 없거나 클라이언트 생성이 안 되었을 때 빠른 예외 처리
        if not client:
            return make_kakao_response("API 키 설정 확인이 필요합니다.")

        # Groq 초고속 8B 모델 호출 + 타임아웃 극단적 방지를 위한 극소 토큰 설정
        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # 가장 빠르고 가벼운 8B 초고속 모델
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=120,    # 짧은 답변으로 출력 생성 시간을 0.5초 이내로 단축
            temperature=0.5
        )

        ai_reply = chat_completion.choices[0].message.content.strip()
        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Error handling request: {e}")
        # 오류/지연 발생 시 5초 이내에 안전하게 기본 안내문 반환
        return make_kakao_response("KAL 등산회 대장 로봇입니다! 준비 중이니 잠시 후 다시 질문해 주세요.")

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
    app.run(host='0.0.0.0', port=5000)
