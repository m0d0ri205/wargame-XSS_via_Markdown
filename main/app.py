from flask import Flask, request, render_template, session, abort
import re
import secrets
import os
from functools import wraps
from datetime import datetime
import html

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 플래그 파일 읽기
with open("flag.txt", "r") as f:
    FLAG = f.read().strip()

def markdown_to_html(content):
    # 1. 먼저 마크다운 문법을 HTML로 변환
    content = re.sub(r'!\[([^\]]+)\]\((.+)\)', r'<img alt="\1" src="\2">', content)
    content = re.sub(r'\[([^\]]+)\]\((.+)\)', r'<a href="\2">\1</a>', content)
    
    # 2. 마크다운으로 생성된 태그들을 임시로 보호
    img_placeholder = "___MARKDOWN_IMG_SAFE___"
    link_placeholder = "___MARKDOWN_LINK_SAFE___"
    
    protected_imgs = []
    protected_links = []
    
    # 마크다운으로 생성된 img 태그 보호
    def protect_img(match):
        protected_imgs.append(match.group(0))
        return f"{img_placeholder}{len(protected_imgs)-1}{img_placeholder}"
    
    # 마크다운으로 생성된 a 태그 보호  
    def protect_link(match):
        protected_links.append(match.group(0))
        return f"{link_placeholder}{len(protected_links)-1}{link_placeholder}"
    
    content = re.sub(r'<img[^>]*>', protect_img, content)
    content = re.sub(r'<a[^>]*>.*?</a>', protect_link, content, flags=re.DOTALL)
    
    # 3. 모든 HTML 태그 이스케이프
    content = html.escape(content)
    
    # 4. 보호된 마크다운 태그들 복원
    for i, img_tag in enumerate(protected_imgs):
        content = content.replace(f"{img_placeholder}{i}{img_placeholder}", img_tag)
    
    for i, link_tag in enumerate(protected_links):
        content = content.replace(f"{link_placeholder}{i}{link_placeholder}", link_tag)
    
    # 5. 줄바꿈 변환
    content = content.replace('\n', '<br>')
    return content



# 방법 1: XSS를 통해서만 접근 가능 (JavaScript에서만 접근)
def require_xhr_or_fetch(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # XMLHttpRequest나 fetch API를 통한 요청만 허용
        if not (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                'application/json' in request.headers.get('Accept', '') or
                request.headers.get('Sec-Fetch-Mode') == 'cors'):
            abort(403, "Direct access forbidden")
        return f(*args, **kwargs)
    return decorated_function

# 방법 2: 특정 Referer에서만 접근 (같은 도메인의 메인 페이지에서만)
def require_same_origin_referer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        referer = request.headers.get('Referer', '')
        host = request.headers.get('Host', '')
        
        # Referer가 같은 호스트의 메인 페이지여야 함
        if not referer.startswith(f'http://{host}/') and not referer.startswith(f'https://{host}/'):
            abort(403, "Invalid referer")
        return f(*args, **kwargs)
    return decorated_function

# 방법 3: POST 요청 + JSON 데이터만 허용
def require_post_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method != 'POST':
            abort(405, "Method not allowed")
        
        # Content-Type이 application/json이어야 함
        if not request.is_json:
            abort(400, "JSON required")
        return f(*args, **kwargs)
    return decorated_function

# 방법 4: 특정 헤더 조합 요구
def require_special_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # JavaScript에서 설정할 수 있는 특별한 헤더 조합
        if not (request.headers.get('X-Custom-Header') == 'XSS-Attack' and
                request.headers.get('X-Flag-Request') == 'true'):
            abort(403, "Missing required headers")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("markdown", "")
        rendered_html = markdown_to_html(user_input)
        return render_template("index.html", rendered_html=rendered_html)
    return render_template("index.html", rendered_html="")

# 방법 1 적용: fetch/XMLHttpRequest를 통해서만 접근
@app.route("/flag", methods=["GET"])
@require_xhr_or_fetch
def flag():
    return FLAG

# 방법 2 적용: 같은 도메인 Referer 필요
@app.route("/flag-referer", methods=["GET"])
@require_same_origin_referer
def flag_referer():
    return FLAG

# 방법 3 적용: POST + JSON만 허용
@app.route("/flag-post", methods=["POST"])
@require_post_json
def flag_post():
    return FLAG

# 방법 4 적용: 특별한 헤더 조합 필요
@app.route("/flag-headers", methods=["GET"])
@require_special_headers
def flag_headers():
    return FLAG

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = ""
    return response

if __name__ == "__main__":
    port = int(os.environ.get('port', 5000))
    app.run(host="0.0.0.0", port=port)