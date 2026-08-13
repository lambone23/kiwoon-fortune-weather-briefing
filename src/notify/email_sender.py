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

def build_notification_email(
    title: str,
    message_lines: list[str],
    manage_link: str = None,
    accent_color: str = "#3D4B6E",
) -> str:
    """
    카드형 알림 메일 공통 템플릿. 챕터11에서 확정한 화이트+인디고 톤 반영.
    - 다크모드 메타태그 제거 (라이트 테마 고정, 사용자 메일앱 다크모드에 따른
      의도치 않은 색 반전 방지).
    - icon 파라미터 제거 (로고·이모지 전면 배제 결정에 따라 더 이상 쓰이지 않음).
    - manage_link가 없으면(탈퇴 완료 등 이후 관리할 계정이 없는 경우) 관리
      링크 문단 자체를 생략.
    - accent_color는 호출부가 유형별로 지정 (가입완료/정보수정: 인디고,
      알림On: 초록, 알림Off: 주황, 탈퇴: 빨강 — 12-2-2에서 확정).
    """
    lines_html = "".join(
        f'<p style="margin:0 0 10px 0; color:#2B2A27; font-size:13px; line-height:1.6;">{line}</p>'
        for line in message_lines
    )

    manage_html = (
        f'''<p style="margin:16px 0 0 0; font-size:11px; color:#8A8578; line-height:1.6;">
            관리 링크는 본인 확인용 비밀 링크예요. 다른 사람에게 공유하지 마세요.<br>
            <a href="{manage_link}" style="color:#3D4B6E;">내 정보 관리하기</a>
        </p>'''
        if manage_link else ""
    )

    return f"""
    <div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif; max-width:420px; margin:0 auto; background-color:#FAF9F6; padding:20px; border-radius:14px;">

        <p style="text-align:center; font-size:16px; font-weight:500; color:#2B2A27; margin:0 0 4px;">KI WOON 기운</p>
        <p style="text-align:center; font-size:11px; color:#8A8578; margin:0 0 18px;">오늘의 운세와 날씨를 전하는 브리핑 서비스</p>

        <div style="background-color:#FFFFFF; border:0.5px solid #E4E1D8; border-radius:12px; overflow:hidden;">
            <div style="background-color:{accent_color}; padding:12px 16px;">
                <span style="font-size:14px; font-weight:500; color:#FFFFFF;">{title}</span>
            </div>
            <div style="background-color:#FFFFFF; padding:16px;">
                {lines_html}
                {manage_html}
            </div>
        </div>

        <p style="text-align:center; font-size:10px; color:#B5B2A8; margin-top:16px;">
            문의 : lambone234567@gmail.com<br>
            © 2026 Kiwoon. All rights reserved.
        </p>
    </div>
    """


if __name__ == "__main__":
    send_email(
        to_email="본인이메일주소@example.com",
        subject="Kiwoon 테스트 메일 (HTML+텍스트)",
        html_body="<p>이것은 <b>HTML 테스트</b>입니다. <a href='https://google.com'>구글 링크</a></p>",
        text_body="이것은 텍스트 테스트입니다. 구글 링크: https://google.com",
    )
    print("메일 발송 완료")