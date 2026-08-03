"""
이메일 발송 모듈.
- Gmail SMTP를 이용해 이메일을 발송.
- SMTP_EMAIL(발송 계정), SMTP_APP_PASSWORD(앱 비밀번호)는 .env에서 로드.
- HTML 본문과 순수 텍스트 본문을 함께 보내는 multipart/alternative 구조.
  이메일 클라이언트가 HTML을 지원하면 카드형 디자인을, 지원 안 하면
  텍스트 버전을 자동으로 보여줌. HTML이 깨지는 경우에도 텍스트 버전이
  안전망 역할을 함.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_DISPLAY_NAME = "Kiwoon"


def send_email(to_email: str, subject: str, html_body: str, text_body: str = None) -> None:
    """
    to_email로 이메일 한 통을 발송. HTML과 텍스트 버전을 함께 보냄.

    Args:
        to_email: 받는 사람 이메일 주소
        subject: 메일 제목
        html_body: 메일 본문 (HTML 형식, 카드형 디자인 등)
        text_body: 메일 본문 (순수 텍스트, HTML 미지원 클라이언트용 대체 버전).
                   생략하면 안내 문구만 담은 단순 버전을 사용.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_DISPLAY_NAME} <{SMTP_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    if text_body is None:
        text_body = "이 메일은 HTML 형식으로 작성되었습니다. HTML을 지원하는 메일 앱에서 확인해주세요."

    # multipart/alternative는 "나중에 추가한 파트"를 우선 표시하는 관례가 있어
    # 반드시 text를 먼저, html을 나중에 attach함 (HTML 지원 클라이언트가 HTML을 보여주도록)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.send_message(msg)


if __name__ == "__main__":
    send_email(
        to_email="본인이메일주소@example.com",
        subject="Kiwoon 테스트 메일 (HTML+텍스트)",
        html_body="<p>이것은 <b>HTML 테스트</b>입니다. <a href='https://google.com'>구글 링크</a></p>",
        text_body="이것은 텍스트 테스트입니다. 구글 링크: https://google.com",
    )
    print("메일 발송 완료")