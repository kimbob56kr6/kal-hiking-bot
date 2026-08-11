kal hiking boss program
✅ 1단계 — GitHub에 있는 코드가 실행 가능한지 확인하기
지금 네 GitHub repo에 있는 파일은:

main.py

requirements.txt

README.md

여기서 main.py가 실제로 웹서버로 동작해야 Render에서 실행할 수 있어.

즉, main.py 안에 Flask 서버 시작 코드가 있어야 한다.

✔️ main.py에 반드시 있어야 하는 코드
아래 코드가 main.py 맨 아래에 있어야 한다:

python
if __name__ == "__main__":
   
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 
