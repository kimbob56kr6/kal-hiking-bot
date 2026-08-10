import os
import logging
from flask import Flask, request, jsonify
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Groq API 설정 — 절대 소스에 실제 키를 하드코딩하지 마세요.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY 환경변수가 설정되어 있지 않습니다. 배포 환경에서 반드시 설정하세요.")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    req = request.get_json(silent=True) or {}
    # 카카오톡 사용자의 발화(질문) 추출
    user_message = req.get('userRequest', {}).get('utterance', '')
    if not user_message:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "질문을 인식하지 못했습니다."}}]}
        }), 400

    # Groq API 호출
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}" if GROQ_API_KEY else "",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "당신은 KAL 등산회의 인공지능 대장 로봇입니다. 쾌활하고 친절하게 답변하세요."},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        body = res.json()
        # 안전하게 응답 파싱
        choices = body.get("choices", [])
        if choices and isinstance(choices, list):
            ai_answer = choices[0].get("message", {}).get("content", "").strip() or "대답을 생성하지 못했습니다."
        else:
            ai_answer = "대장 AI 응답 포맷을 해석하지 못했습니다."
    except requests.exceptions.RequestException as e:
        logger.exception("Groq API 호출 중 오류")
        ai_answer = "대장 AI 응답 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    except ValueError:
        logger.exception("Groq 응답 JSON 파싱 실패")
        ai_answer = "응답을 해석하는 중 오류가 발생했습니다."

    # 카카오톡 스킬 규격 응답 포맷 생성
    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": ai_answer
                    }
                }
            ]
        }
    }
    return jsonify(response_body)

if __name__ == '__main__':
    # 개발용: 실제 배포에서는 WSGI 서버(uvicorn/gunicorn 등)를 사용하세요.
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
