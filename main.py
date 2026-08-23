from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Groq API 키 직접 입력
GROQ_API_KEY = "gsk_yocptA3I4yosUHowNWM3WGdyb3FYM3WC43L1SL34IYWnV0f"

SYSTEM_PROMPT = """너는 애틀랜타 KAL 하이킹팀의 AI 대장이야.
회원들에게 일정, 난이도, 준비물, 날씨, 코스 추천을 짧고 친절하게 한국어로 알려줘."""

@app.route("/", methods=["GET"])
def home():
    return "KAL 하이킹 AI 대장 서버 정상 작동 중", 200

@app.route("/kakao", methods=["POST"])
def kakao():
    user_message = "안녕하세요"

    # 1. 카카오톡 요청 데이터 파싱
    try:
        body = request.get_json(force=True, silent=True) or {}
        user_message = (
            body.get("userRequest", {}).get("utterance")
            or body.get("action", {}).get("params", {}).get("user_message")
            or "안녕하세요"
        )
    except Exception:
        user_message = "안녕하세요"

    reply_text = ""

    # 2. Groq API 호출
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
        }
        groq_res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=8,
        )

        if groq_res.status_code == 200:
            groq_data = groq_res.json()
            reply_text = groq_data.get("choices", [{}])[0].get("message", {}).get("content", "안녕하세요! KAL 하이킹 AI 대장입니다.")
        else:
            reply_text = "안녕하세요! KAL 하이킹 AI 대장입니다. 잠시 후 다시 질문해 주세요."
    except Exception:
        reply_text = "안녕하세요! KAL 하이킹 AI 대장입니다. 무엇을 도와드릴까요?"

    # 3. 카카오톡 v2.0 공식 표준 응답 반환
    kakao_response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": reply_text
                    }
                }
            ]
        }
    }

    return jsonify(kakao_response), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
