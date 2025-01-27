# Python slim 패키지 사용
FROM python:slim

# 환경 변수 설정
ENV port 8000
#한국 시간
ENV TZ Asia/Seoul

# 애플리케이션 디렉토리 생성 및 이동
WORKDIR /usr/src/app

# 애플리케이션 소스 코드 및 의존성 설치
COPY ./requirements.txt ./
COPY ./main ./
RUN apt-get update 
RUN pip install --no-cache-dir -r requirements.txt

# 일반 유저로 실행
RUN apt-get update
RUN apt-get install -y git
RUN groupadd -g 999 appuser
RUN useradd -r -u 999 -g appuser appuser

#RUN chown -R appuser:appuser /usr/src/app/logs
#RUN chmod 644 /usr/src/app/logs

USER appuser

# 포트 노출
EXPOSE $port

# 애플리케이션 실행.
CMD ["sh", "-c", "python ./app.py >> /proc/1/fd/1  2>&1"]
