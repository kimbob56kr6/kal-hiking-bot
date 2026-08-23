from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

SYSTEM_PROMPT = """너는 애틀랜타 KAL 하이킹팀의 AI 대장이야.
회원들에게 일정, 난이도, 준비물, 날씨, 코스 추천을 짧고 친절하게 한국어로 알려줘."""

@app.route("/", methods=["GET"])
def home():
    return "KAL 하이킹 AI 대장 서버 정상 작동 중", 200

@app.route("/kakao", methods=["POST"])
def kakao():
    user_message = "안녕하세요"
    
    # 1. 카카오톡 요청 파싱 예외 처리
    try:
        body = request.get_json(silent=True) or {}
        user_message = (
            body.get("userRequest", {}).get("utterance")
            or body.get("action", {}).get("params", {}).get("user_message")
            or "안녕하세요"
        )
    except Exception:
        user_message = "안녕하세요"

    reply_text = "안녕하세요! KAL 하이킹 AI 대장입니다."

    # 2. Groq API 호출
    api_key = GROQ_API_KEY.strip()
    if api_key:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
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
                timeout=8
            )

            if groq_res.status_code == 200:
                groq_data = groq_res.json()
                reply_text = groq_data["choices"][0]["message"]["content"]
            else:
                reply_text = f"안녕하세요! KAL 하이킹 AI 대장입니다. (API 응답 오류: {groq_res.status_code})"
        except Exception as e:
            reply_text = "안녕하세요! KAL 하이킹 AI 대장입니다. 무엇을 도와드릴까요?"
    else:
        reply_text = "GROQ_API_KEY가 설정되지 않았습니다."

    # 3. 카카오톡 v2.0 규격 응답 생성
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
