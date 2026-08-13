import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google import genai

# ================================
# 1. 환경 변수 로드
# ================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)

# ================================
# 2. 시스템 프롬프트
# ================================
SYSTEM_PROMPT = (
    "너는 아틀란타 KAL 하이킹팀의 Hiking 대장이야. "
    "회원들의 질문에 대해 핵심만 1~2문장으로 아주 짧고 친절하게 한국어로 답변해줘."
)

# ================================
# 3. 기본 라우트
# ================================
@app.route('/', methods=['GET'])
def home():
    return "KAL Hiking Bot is running!"

# ================================
# 4. Kakao Skill 엔드포인트
# ================================
@app.route('/kakao', methods=['POST'])
def kakao_skill():
    try:
        req_data = request.get_json() or {}

        # 카카오톡 입력 메시지
        user_message = req_data.get('userRequest', {}).get('utterance', '').strip()
        if not user_message:
            user_message = "안녕하세요"

        if not client:
            return make_kakao_response("Gemini API 키가 설정되지 않았습니다.")

        # ================================
        # 🔥 interactions.create() 초고속 최적화 버전
        # ================================
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            system_instruction=SYSTEM_PROMPT,
            input=user_message,
            config={
                "response_modalities": ["text"],   # 텍스트만 생성 → 속도 증가
                "temperature": 0.2,                # 계산량 감소 → 속도 증가
                "max_output_tokens": 60,           # 짧은 답변 → 속도 증가
                "top_p": 0.8,                      # 샘플링 안정화 → 속도 증가
                "candidate_count": 1              
