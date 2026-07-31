"""
이메일 발송 모듈.
- Gmail SMTP를 이용해 이메일을 발송.
- SMTP_EMAIL(발송 계정), SMTP_APP_PASSWORD(앱 비밀번호)는 .env에서 로드.
- 본문은 HTML 형식 지원 (하이퍼링크 등 서식 포함 가능).
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


def send_email(to_email: str, subject: str, html_body: str) -> None:
    """
    to_email로 HTML 형식 이메일 한 통을 발송.
    """
    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_DISPLAY_NAME} <{SMTP_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.send_message(msg)


if __name__ == "__main__":
    send_email(
        to_email="lambone234567@gmail.com",
        subject="Kiwoon 테스트 메일 (HTML)",
        html_body="<p>이것은 <b>HTML 테스트</b>입니다. <a href='https://google.com'>구글 링크</a></p>",
    )
    print("메일 발송 완료")