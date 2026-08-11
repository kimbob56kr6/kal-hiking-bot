import os
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Groq 클라이언트 초기화 (Render의 Environment Variable에 설정된 API 키 사용)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# AI 로봇 시스템 프롬프트 (KAL 등산회 안내 대장)
SYSTEM_PROMPT = """
너는 '애틀랜타 KAL 등산회'의 AI 등산 대장이야. 
회원들에게 친절하고 명확하며 위트 있게 등산 일정과 안내를 제공해줘.
카카오톡 챗봇 특성상 너무 길지 않게 2~3문장 이내로 핵심만 답변해줘.
"""

# 1. 브라우저 접속 시 헬스체크용 루트 경로 (Render 무한 로딩 방지)
@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running successfully!"

# 2. 카카오톡 스킬 수신 전용 엔드포인트
@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json()
        
        # 카카오톡 발화 문장 추출
        user_message = req_data.get('userRequest', {}).get('utterance', '')
        if not user_message:
            user_message = "안녕하세요"

        # API 키 미설정 예외 처리
        if not client:
            return make_kakao_response("GROQ_API_KEY가 설정되지 않았습니다.")

        # Groq API 호출 (5초 제한에 맞춘 초고속 모델 및 토큰 제한 적용)
        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # 초고속 8B 모델 사용 (응답 속도 1초 미만)
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=250,  # 답변 길이를 제한하여 빠른 응답 보장
            temperature=0.7
        )

        ai_reply = chat_completion.choices[0].message.content.strip()
        return make_kakao_response(ai_reply)

    except Exception as e:
        print(f"Error during execution: {e}")
        # 오류 시 카카오톡 타임아웃 방지를 위한 기본 안내
        return make_kakao_response("죄송합니다. 요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

# 카카오톡 규격에 맞는 JSON 응답 생성 함수
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
    # 로컬 테스트용
    app.run(host='0.0.0.0', port=5000, debug=True)