"""
스케줄링 로직 모듈.
- 매일 정해진 시간에 "오늘의 운세" 이메일을 자동 발송하는 배치 작업.
- 발송 로직(누구에게 뭘 보낼지 찾고, 계산하고, 메일 보내는 부분)과
  이 로직을 호출하는 방식(APScheduler vs 외부 Cron)을 분리해서 설계함.
"""
import os
import re
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import Subscriber
from src.saju.calculator import get_saju, get_saju_from_lunar, format_saju_summary
from src.llm.fortune_generator import generate_fortune
from src.notify.email_sender import send_email
from src.weather.weather_fetcher import get_weather_by_region, format_weather_summary

FORTUNE_LABELS = ["총운", "재물운", "학업운", "직업운", "건강운", "연애운",
                  "행운 컬러", "행운 소재", "행운 방향"]


def _parse_fortune_sections(fortune_text: str) -> dict:
    """
    generate_fortune()이 만든 텍스트를 항목별(총운/재물운/.../행운 방향)로
    분리해서 딕셔너리로 반환. 각 항목을 개별적으로 스타일링하기 위함.
    """
    label_pattern = "|".join(FORTUNE_LABELS)
    pattern = rf"({label_pattern}):\s*(.*?)(?=(?:{label_pattern}):|$)"
    matches = re.findall(pattern, fortune_text, re.DOTALL)
    return {label: content.strip() for label, content in matches}


def _build_text_body(subscriber: Subscriber, weather_text: str, fortune_text: str, manage_link: str) -> str:
    """
    순수 텍스트 버전 본문 조립 (HTML 미지원 클라이언트 대비 안전망).
    """
    return f"""안녕하세요, Kiwoon입니다.
오늘의 운세와 날씨를 전해드릴게요.

[오늘의 날씨 - {subscriber.region_1} {subscriber.region_2}]
{weather_text}

[오늘의 운세]
{fortune_text}

---
지역, 생년월일시, 알림 시간 등 정보를 바꾸고 싶으시면 아래 링크에서 관리하실 수 있어요:
{manage_link}

이 링크는 비밀번호와 같은 역할을 합니다. 다른 사람과 공유하지 마세요.

감사합니다.
"""


def _build_html_body(subscriber: Subscriber, weather_text: str, fortune_text: str, manage_link: str) -> str:
    """
    카드형 HTML 본문 조립. 총운은 강조 박스, 재물운~연애운은 항목별 간격,
    행운 컬러/소재/방향은 구분선 아래 아이콘과 함께 정리.
    실제 이메일 클라이언트는 CSS 변수를 지원하지 않으므로 색상은 고정 hex로 처리.
    """
    weather_lines = weather_text.replace("\n", "<br>")
    sections = _parse_fortune_sections(fortune_text)

    main_items = ["재물운", "학업운", "직업운", "건강운", "연애운"]
    main_html = "".join(
        f'<div style="margin-bottom:12px;"><b>{label}</b><br>{sections.get(label, "")}</div>'
        for label in main_items
    )

    luck_icons = {"행운 컬러": "🎨", "행운 소재": "🧵", "행운 방향": "🧭"}
    luck_html = "".join(
        f'<div>{icon} <b>{label}</b> · {sections.get(label, "")}</div>'
        for label, icon in luck_icons.items()
    )

    total_html = f"""
    <div style="margin-bottom:16px; padding:12px 14px; background:#F3EFFC; border-radius:12px;">
        <div style="font-size:15px; font-weight:bold; color:#5B3FA0; margin-bottom:4px;">✨ 총운</div>
        <div>{sections.get("총운", "")}</div>
    </div>
    """

    return f"""
<div style="max-width:520px; margin:0 auto; font-family:'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;">

  <p style="margin:0 0 4px 0; font-size:15px; color:#333;">안녕하세요, Kiwoon입니다.</p>
  <p style="margin:0 0 16px 0; font-size:15px; color:#333;">오늘의 운세와 날씨를 전해드릴게요.</p>

  <div style="border-radius:12px; overflow:hidden; border:1px solid #e0e0e0; margin-bottom:12px;">
    <div style="background-color:#4A90D9; padding:14px 18px;">
      <div style="font-size:16px; font-weight:bold; color:#ffffff;">☀️ 오늘의 날씨</div>
      <div style="font-size:13px; color:#e8f1fb;">{subscriber.region_1} {subscriber.region_2}</div>
    </div>
    <div style="background-color:#ffffff; padding:16px 18px; font-size:14px; color:#333; line-height:1.7;">
      {weather_lines}
    </div>
  </div>

  <div style="border-radius:12px; overflow:hidden; border:1px solid #e0e0e0; margin-bottom:16px;">
    <div style="background-color:#8A5CD9; padding:14px 18px;">
      <div style="font-size:16px; font-weight:bold; color:#ffffff;">🔮 오늘의 운세</div>
    </div>
    <div style="background-color:#ffffff; padding:18px; font-size:14px; color:#333; line-height:1.7;">
      {total_html}
      {main_html}
      <div style="border-top:1px solid #e0e0e0; padding-top:12px; font-size:13px; color:#555;">
        {luck_html}
      </div>
    </div>
  </div>

  <p style="margin:0 0 4px 0; font-size:13px; color:#555;">
    지역, 생년월일시, 알림 시간 등 정보를 바꾸고 싶으시면 아래 링크에서 관리하실 수 있어요:
  </p>
  <p style="margin:0 0 12px 0; font-size:12px; color:#999;">
    ⚠️ 이 링크는 비밀번호와 같은 역할을 합니다. 다른 사람과 공유하지 마세요.
  </p>
  <a href="{manage_link}" style="display:inline-block; padding:10px 18px; background-color:#333; color:#ffffff; text-decoration:none; border-radius:8px; font-size:13px;">
    내 정보 관리하기
  </a>

  <p style="margin:32px 0 0 0; font-size:13px; color:#555;">감사합니다.</p>

  <p style="margin:24px 0 0 0; font-size:12px; color:#999;">
    문의사항이 있으시면 아래 이메일로 알려주세요:<br>
    <a href="mailto:lambone234567@gmail.com" style="color:#999;">lambone234567@gmail.com</a>
  </p>

</div>
"""

def get_due_subscribers(db: Session) -> list[Subscriber]:
    """
    현재 시각(HH:MM)과 notify_time이 일치하고, notify_enabled=True인
    구독자 목록을 DB에서 조회.

    Returns:
        list[Subscriber]: 지금 발송 대상인 구독자 리스트
    """
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")

    subscribers = db.query(Subscriber).filter(
        Subscriber.notify_enabled == True,
        Subscriber.notify_time == current_time_str,
    ).all()

    return subscribers


def send_fortune_to_subscriber(subscriber: Subscriber) -> None:
    """
    구독자 한 명에게 오늘의 운세 + 날씨를 계산해서 이메일로 발송.
    """
    if subscriber.calendar_type == "음력":
        saju = get_saju_from_lunar(
            subscriber.birth_year, subscriber.birth_month, subscriber.birth_day,
            subscriber.birth_hour, subscriber.birth_minute,
        )
    else:
        saju = get_saju(
            subscriber.birth_year, subscriber.birth_month, subscriber.birth_day,
            subscriber.birth_hour, subscriber.birth_minute,
        )

    summary = format_saju_summary(saju)
    fortune_text = generate_fortune(saju, summary, gender=subscriber.gender)

    weather_summary = get_weather_by_region(subscriber.region_1, subscriber.region_2)
    weather_text = format_weather_summary(weather_summary)

    manage_link = f"{os.getenv('BASE_URL')}/manage/{subscriber.manage_token}"

    text_body = _build_text_body(subscriber, weather_text, fortune_text, manage_link)
    html_body = _build_html_body(subscriber, weather_text, fortune_text, manage_link)

    send_email(
        to_email=subscriber.email,
        subject="[Kiwoon] 오늘의 운세 & 날씨 브리핑",
        html_body=html_body,
        text_body=text_body,
    )
    
def send_daily_fortunes() -> None:
    """
    지금 이 시각에 알림을 받기로 한 모든 구독자에게 오늘의 운세를 발송.
    - 스케줄러(APScheduler든 외부 Cron이든)가 호출하는 최종 진입점 함수.
    - 한 명 발송이 실패해도 나머지 발송은 계속 진행되도록 개별 예외 처리.
    """
    db = SessionLocal()
    try:
        due_subscribers = get_due_subscribers(db)
        print(f"[스케줄러] 발송 대상 {len(due_subscribers)}명 확인됨")

        for subscriber in due_subscribers:
            try:
                send_fortune_to_subscriber(subscriber)
                print(f"[스케줄러] 발송 성공: {subscriber.email}")
            except Exception as e:
                print(f"[스케줄러] 발송 실패: {subscriber.email}, 사유: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    send_daily_fortunes()