"""
스케줄링 로직 모듈.
- 매일 정해진 시간에 "오늘의 운세" 이메일을 자동 발송하는 배치 작업.
- 발송 로직(누구에게 뭘 보낼지 찾고, 계산하고, 메일 보내는 부분)과
  이 로직을 호출하는 방식(APScheduler vs 외부 Cron)을 분리해서 설계함.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import Subscriber
from src.saju.calculator import get_saju, get_saju_from_lunar, format_saju_summary
from src.llm.fortune_generator import generate_fortune
from src.notify.email_sender import send_email


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
    구독자 한 명에게 오늘의 운세를 계산해서 이메일로 발송.

    Args:
        subscriber: 발송 대상 구독자 (Subscriber 모델 인스턴스)
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

    send_email(
        to_email=subscriber.email,
        subject="[Kiwoon] 오늘의 운세 브리핑",
        html_body=f"""
        <p>안녕하세요, Kiwoon입니다.</p>
        <p>오늘의 운세를 전해드릴게요.</p>
        <pre style="white-space: pre-wrap; font-family: inherit;">{fortune_text}</pre>
        <p>감사합니다.</p>
        """,
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