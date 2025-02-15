from flask import Flask, request, render_template
import re

app = Flask(__name__)

# 플래그 파일 읽기
with open("flag.txt", "r") as f:
    FLAG = f.read().strip()

# 취약한 마크다운 렌더링 함수
def markdown_to_html(content):
    # 이미지 태그 변환
    content = re.sub(r'!\[([^\]]+)\]\((.+)\)', r'<img alt="\1" src="\2">', content)
    # 링크 태그 변환
    content = re.sub(r'\[([^\]]+)\]\((.+)\)', r'<a href="\2">\1</a>', content)
    # 줄바꿈 변환
    content = content.replace('\n', '<br>')
    return content


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("markdown", "")
        # 마크다운을 HTML로 변환
        rendered_html = markdown_to_html(user_input)
        return render_template("index.html", rendered_html=rendered_html)
    return render_template("index.html", rendered_html="")


@app.route("/flag", methods=["GET"])
def flag():
    return FLAG


@app.after_request
def add_security_headers(response):
    # CSP를 완전히 제거하여 XSS 테스트 가능
    response.headers['Content-Security-Policy'] = ""
    return response


if __name__ == "__main__":
    # 디버그 모드 활성화
    app.run(host="0.0.0.0", port=5000)
