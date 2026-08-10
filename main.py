import os
import logging
import time
from typing import Dict, List
from flask import Flask, request, jsonify
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 환경 변수
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
# 선택적: Kakao webhook 검증용 시크릿(설정하면 서명 검증을 활성화하세요)
KAKAO_WEBHOOK_SECRET = os.environ.get("KAKAO_WEBHOOK_SECRET")

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY가 설정되어 있지 않습니다. 실제 배포 환경에서 반드시 설정하세요.")

# 간단한 메모리 기반 세션 컨텍스트(프로덕션에서는 Redis 같은 외부 저장소 권장)
# 구조: {user_id: [(role, text), ...]}
conversation_context: Dict[str, List[Dict[str, str]]] = {}
CONTEXT_MAX_LEN = 6  # 최근 메시지 개수

SYSTEM_PROMPT = (
    "당신은 KAL 등산회의 인공지능 대장 로봇입니다. 쾌활하고 친절하게, 간결하게 답변하세요."
)


def query_groq(messages, timeout=15):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        # 필요하면 max_tokens, temperature 등 파라미터를 추가하세요
    }

    try:
        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
        res.raise_for_status()
        body = res.json()
        choices = body.get("choices", [])
        if choices and isinstance(choices, list):
            return choices[0].get("message", {}).get("content", "").strip()
        logger.error("Groq 응답에 choices 없음: %s", body)
        return None
    except requests.exceptions.RequestException as e:
        logger.exception("Groq API 호출 오류")
        return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": int(time.time())})


@app.route('/kakao', methods=['POST'])
def kakao_skill():
    # 카카오의 요청 포맷을 안전하게 파싱
    raw = request.get_data(as_text=True)
    try:
        req = request.get_json(silent=True) or {}
    except Exception:
        logger.exception("요청 JSON 파싱 실패")
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "요청을 처리할 수 없습니다."}}]}}), 400

    # (선택) 서명 검증 — KAKAO_WEBHOOK_SECRET이 설정되어 있을 때만 동작합니다.
    # Kakao의 실제 서명 헤더 이름은 사용중인 플랫폼에 따라 다르므로, 설정에 맞게 수정하세요.
    # 예시(미활성화):
    # signature = request.headers.get('Kakao-Signature')
    # if KAKAO_WEBHOOK_SECRET and not verify_signature(raw, signature, KAKAO_WEBHOOK_SECRET):
    #     return jsonify({"version":"2.0","template":{"outputs":[{"simpleText":{"text":"서명 검증 실패"}}]}}), 401

    # 카카오 user id 및 발화를 추출
    user_id = None
    user_message = ""
    try:
        user_id = req.get('userRequest', {}).get('user', {}).get('id')
        user_message = req.get('userRequest', {}).get('utterance', '')
    except Exception:
        user_message = ''

    if not user_message:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "질문을 인식하지 못했습니다. 다시 입력해 주세요."}}]}
        }), 400

    # 대화 컨텍스트에 사용자 메시지 추가
    if user_id:
        conversation_context.setdefault(user_id, [])
        conversation_context[user_id].append({"role": "user", "content": user_message})
        # 길이 제한
        if len(conversation_context[user_id]) > CONTEXT_MAX_LEN:
            conversation_context[user_id] = conversation_context[user_id][-CONTEXT_MAX_LEN:]

    # Groq에 보낼 메시지 구성: system + recent context
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if user_id:
        for m in conversation_context.get(user_id, []):
            messages.append({"role": m["role"], "content": m["content"]})
    else:
        messages.append({"role": "user", "content": user_message})

    # Groq 호출
    ai_answer = query_groq(messages)
    if ai_answer is None:
        ai_answer = "대장 AI 응답 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    # 컨텍스트에 AI 응답 추가
    if user_id:
        conversation_context[user_id].append({"role": "assistant", "content": ai_answer})
        if len(conversation_context[user_id]) > CONTEXT_MAX_LEN:
            conversation_context[user_id] = conversation_context[user_id][-CONTEXT_MAX_LEN:]

    # 카카오 스킬 응답 포맷: simpleText와 함께 quickReplies(원하면) 제공
    response_body = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {"text": ai_answer}
                }
            ],
            # optional quickReplies: 카카오가 지원하는 형식에 맞게 변경할 수 있습니다.
            "quickReplies": [
                {"messageText": "등산 코스 추천", "action": "message", "label": "코스 추천"},
                {"messageText": "장비 체크리스트", "action": "message", "label": "장비"},
                {"messageText": "다음 모임 일정", "action": "message", "label": "일정"}
            ]
        }
    }

    return jsonify(response_body)


if __name__ == '__main__':
    # 개발용 로컬 실행
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
