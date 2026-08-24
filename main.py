from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# 텔레그램 토큰 및 Groq API 키
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8979306686:AAFqBLi3NFyf8GT5O5Ku-oRPPOhrEOpKTVc")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_yocptA3I4yosUHowNWM3WGdyb3FYM3WC43L1SL34IYWnV0f")

SYSTEM_PROMPT = """너는 애틀랜타 KAL 하이킹팀의 AI 대장이야.
회원들에게 일정, 난이도, 준비물, 날씨, 코스 추천을 짧고 친절하게 한국어로 알려줘."""

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Send Error: {e}")

@app.route("/", methods=["GET"])
def home():
    return "KAL 하이킹 텔레그램 AI 대장 서버 작동 중", 200

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True, silent=True) or {}
    
    # 메시지 데이터 추출
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_text = message.get("text", "")

    if not chat_id or not user_text:
        return jsonify({"status": "ok"}), 200

    # Groq API 호출
    reply_text = "안녕하세요! KAL 하이킹 AI 대장입니다."
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0.7,
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=8
        )
        if res.status_code == 200:
            reply_text = res.json()["choices"][0]["message"]["content"]
        else:
            reply_text = f"AI 대장 응답 지연 중입니다. (Error: {res.status_code})"
    except Exception:
        reply_text = "안녕하세요! KAL 하이킹 AI 대장입니다. 잠시 후 다시 질문해 주세요."

    # 텔레그램으로 답장 전송
    send_telegram_message(chat_id, reply_text)
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
