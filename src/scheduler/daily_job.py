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


# 13지지(야자시/조자시 분리) hour → 라벨 매핑.
# frontend/lib/saju/timeBranches.ts의 JIJI_OPTIONS와 동일한 값이어야 함.
# ※ 두 파일(TS/Python)에 같은 정보가 중복 관리되는 상태 — 나중에 시진 구간이
#   바뀌면 양쪽 다 고쳐야 함. 지금은 프론트/백엔드 언어가 달라 공유 모듈을
#   두기 애매해서 중복 유지, 추후 API 엔드포인트로 통합하는 것도 고려 가능.
TIME_BRANCH_BY_HOUR = {
    23: ("야자시", "23:00~00:00"),
    0:  ("조자시", "00:00~01:00"),
    1:  ("축시", "01:00~03:00"),
    3:  ("인시", "03:00~05:00"),
    5:  ("묘시", "05:00~07:00"),
    7:  ("진시", "07:00~09:00"),
    9:  ("사시", "09:00~11:00"),
    11: ("오시", "11:00~13:00"),
    13: ("미시", "13:00~15:00"),
    15: ("신시", "15:00~17:00"),
    17: ("유시", "17:00~19:00"),
    19: ("술시", "19:00~21:00"),
    21: ("해시", "21:00~23:00"),
}


def _get_time_branch_label(hour: int) -> str:
    """
    hour(0~23 또는 None)를 "자시(23:00~00:00)" 형태의 라벨로 변환.
    hour가 None이면(생시 미상) "시간 모름" 반환.
    """
    if hour is None:
        return "시간 모름"
    label, range_str = TIME_BRANCH_BY_HOUR.get(hour, (None, None))
    if label is None:
        return f"{hour}시"  # 예외적으로 매핑에 없는 값이 들어온 경우의 안전장치
    return f"{label}({range_str})"


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
    return f"""KI WOON 기운
오늘의 운세와 날씨를 전하는 브리핑 서비스

안녕하세요, Kiwoon입니다.
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
    sections = _parse_fortune_sections(fortune_text)
    weather_lines = weather_text.split("\n")

    date_line = weather_lines[0] if weather_lines else ""
    temp_line = next((l for l in weather_lines if "최저" in l), "")
    morning_line = next((l for l in weather_lines if l.startswith("오전")), "")
    afternoon_line = next((l for l in weather_lines if l.startswith("오후")), "")

    # "최저 20°C / 최고 31°C" → "↓ 최저 20°C   ↑ 최고 31°C" 형태로 화살표 삽입
    temp_display = temp_line.replace(
        "최저", '<span style="color:#8A8578;">↓</span> 최저'
    ).replace(
        "최고", '<span style="color:#8A8578;">↑</span> 최고'
    )

    main_items = ["재물운", "학업운", "직업운", "건강운", "연애운"]
    main_html = "".join(
        f'<div style="margin-bottom:10px;">'
        f'<p style="margin:0 0 2px; font-size:13px; font-weight:500; color:#2B2A27;">{label}</p>'
        f'<p style="margin:0; font-size:13px; color:#2B2A27; line-height:1.7;">{sections.get(label, "")}</p>'
        f'</div>'
        for label in main_items
    )

    luck_items = ["행운 컬러", "행운 소재", "행운 방향"]
    luck_html = "".join(
        f'<p style="margin:0 0 2px; font-size:13px; font-weight:500; color:#2B2A27;">{label}</p>'
        f'<p style="margin:0 0 10px; font-size:13px; color:#2B2A27; line-height:1.7;">{sections.get(label, "")}</p>'
        for label in luck_items
    )

    total_html = f"""
    <div style="background:#F1EDE4; border-radius:10px; padding:12px 14px; margin-bottom:12px;">
        <p style="font-size:13px; font-weight:500; color:#3D4B6E; margin:0 0 4px;">총운</p>
        <p style="margin:0; font-size:13px; color:#2B2A27; line-height:1.7;">{sections.get("총운", "")}</p>
    </div>
    """

    birth_time_text = _get_time_branch_label(subscriber.birth_hour)
    birth_date_text = f"{subscriber.birth_year}-{subscriber.birth_month:02d}-{subscriber.birth_day:02d}"

    return f"""
<div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif; max-width:420px; margin:0 auto; background-color:#FAF9F6; padding:20px; border-radius:14px;">

  <p style="text-align:center; font-size:16px; font-weight:500; color:#2B2A27; margin:0 0 4px;">KI WOON 기운</p>
  <p style="text-align:center; font-size:11px; color:#8A8578; margin:0 0 18px;">오늘의 운세와 날씨를 전하는 브리핑 서비스</p>

  <div style="background-color:#FFFFFF; border:0.5px solid #E4E1D8; border-radius:12px; overflow:hidden; margin-bottom:12px;">
    <div style="background-color:#3D4B6E; padding:12px 16px;">
      <span style="font-size:14px; font-weight:500; color:#FFFFFF;">오늘의 날씨</span>
      <span style="font-size:11px; color:#C9CFDD; float:right;">{subscriber.region_1} {subscriber.region_2}</span>
    </div>
    <div style="background-color:#FFFFFF; padding:16px; font-size:13px; color:#2B2A27; line-height:2.0;">
      <p style="margin:0 0 8px; font-size:11px; color:#B5B2A8;">{date_line}</p>
      {temp_display}<br>
      {_weather_symbol(morning_line)} {morning_line}<br>
      {_weather_symbol(afternoon_line)} {afternoon_line}
    </div>
  </div>

  <div style="background-color:#FFFFFF; border:0.5px solid #E4E1D8; border-radius:12px; overflow:hidden; margin-bottom:16px;">
    <div style="background-color:#3D4B6E; padding:12px 16px;">
      <span style="font-size:14px; font-weight:500; color:#FFFFFF;">오늘의 운세</span>
      <span style="font-size:11px; color:#C9CFDD; float:right;">{birth_date_text} {birth_time_text}, {subscriber.gender}</span>
    </div>
    <div style="background-color:#FFFFFF; padding:16px;">
      {total_html}
      {main_html}
      <div style="border-top:0.5px solid #E4E1D8; padding-top:10px; margin-top:4px;">
        {luck_html}
      </div>
    </div>
  </div>

  <p style="margin:0 0 6px; font-size:12px; color:#5F5E5A; line-height:1.6; text-align:center;">
    지역·생년월일시·알림 시간은 아래 링크에서 변경할 수 있어요.
  </p>
  <p style="margin:0 0 14px; font-size:11px; color:#8A8578; text-align:center;">
    본인 확인용 비밀 링크이니 공유하지 마세요.
  </p>
  <p style="margin:0; text-align:center;">
    <a href="{manage_link}" style="display:inline-block; padding:9px 16px; background-color:#3D4B6E; color:#FFFFFF; text-decoration:none; border-radius:8px; font-size:13px;">
      내 정보 관리하기
    </a>
  </p>

  <p style="text-align:center; font-size:10px; color:#B5B2A8; margin-top:20px;">
    문의 : lambone234567@gmail.com<br>
    © 2026 Kiwoon. All rights reserved.
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


def _weather_symbol(text: str) -> str:
    """
    날씨 문구(SKY_MAP/PTY_MAP 기반 텍스트)를 유니코드 기호로 매핑.
    프론트 lib/styles/weatherIcon.ts의 getWeatherIcon()과 판별 기준 동일
    (구름많음/흐림은 단계 구분 없이 하나로 통일).
    ※ 이 기호들은 일부 메일 클라이언트(아이폰 Mail 등)에서 컬러 이모지로
    표시될 수 있음 — 챕터11에서 감수하기로 결정된 사항.
    """
    if "맑음" in text:
        return "☀"
    if "비" in text or "소나기" in text:
        return "☂"
    if "눈" in text:
        return "❄"
    if "구름" in text or "흐림" in text:
        return "☁"
    return ""








if __name__ == "__main__":
    send_daily_fortunes()