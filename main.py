import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Groq API 설정
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/kakao', methods=['POST'])
def kakao_skill():
    req = request.get_json()
    
    # 카카오톡 사용자의 발화(질문) 추출
    user_message = req.get('userRequest', {}).get('utterance', '')

    # Groq API 호출
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
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
        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            ai_answer = res.json()['choices'][0]['message']['content']
        else:
            ai_answer = "대장 AI 응답 중 오류가 발생했습니다."
    except Exception as e:
        ai_answer = "죄송합니다, 잠시 후 다시 시도해 주세요!"

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
    app.run(host='0.0.0.0', port=5000)
