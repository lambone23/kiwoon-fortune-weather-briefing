"""
FastAPI 서버 진입점.
- main.py와 동일한 로직(계산→해석)을 웹 요청(JSON)으로 처리.
- calculator.py, prompts.py, fortune_generator.py는 수정 없이 그대로 재사용.
"""

import os
from src.notify.email_sender import send_email

import secrets

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import Subscriber
from src.saju.calculator import get_saju, get_saju_from_lunar, format_saju_summary
from src.llm.fortune_generator import generate_fortune

from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from src.scheduler.daily_job import send_daily_fortunes

app = FastAPI()

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_fortunes, "cron", minute="*")


@app.on_event("startup")
def start_scheduler():
    scheduler.start()
    print("[스케줄러] 시작됨 — 매 분마다 발송 대상 확인")


@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()
    print("[스케줄러] 종료됨")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FortuneRequest(BaseModel):
    calendar_type: str   # "양력" 또는 "음력"
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str          # "남성" 또는 "여성"

class SubscribeRequest(BaseModel):
    email: str
    calendar_type: str
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str
    notify_time: str   # 예: "07:30"
    notify_enabled: bool = True   # 기본값 True (안 보내면 알림 받는 걸로 간주)

class UpdateSubscriberRequest(BaseModel):
    calendar_type: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    gender: Optional[str] = None
    notify_time: Optional[str] = None

class ResendLinkRequest(BaseModel):
    email: str

@app.post("/fortune/preview")
def fortune_preview(req: FortuneRequest):
    if req.calendar_type == "음력":
        saju = get_saju_from_lunar(req.year, req.month, req.day, req.hour, req.minute)
    else:
        saju = get_saju(req.year, req.month, req.day, req.hour, req.minute)

    summary = format_saju_summary(saju)
    fortune_text = generate_fortune(saju, summary, gender=req.gender)

    return {
        "saju_summary": summary,
        "fortune": fortune_text,
    }

@app.post("/subscribe")
def subscribe(req: SubscribeRequest, db: Session = Depends(get_db)):
    existing = db.query(Subscriber).filter(Subscriber.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    manage_token = secrets.token_urlsafe(32)

    new_subscriber = Subscriber(
        email=req.email,
        calendar_type=req.calendar_type,
        birth_year=req.year,
        birth_month=req.month,
        birth_day=req.day,
        birth_hour=req.hour,
        birth_minute=req.minute,
        gender=req.gender,
        notify_time=req.notify_time,
        notify_enabled=req.notify_enabled, # 변경: 고정값 True 대신 사용자 선택값
        manage_token=manage_token,
    )

    db.add(new_subscriber)
    db.commit()
    db.refresh(new_subscriber)

    # ── email 관련 Start ──
    manage_link = f"{os.getenv('BASE_URL')}/manage/{manage_token}"

    if req.notify_enabled:   # 알림 켠 경우에만 메일 발송
        send_email(
            to_email=req.email,
            subject="[Kiwoon] 오늘의 운세 알림 신청이 완료되었습니다",
            html_body=f"""
            <p>안녕하세요, Kiwoon입니다.</p>
            <p>매일 {req.notify_time}에 오늘의 운세 브리핑을 보내드릴게요.</p>
            <p>내 정보 수정 및 알림 끄기는 아래 링크에서 가능합니다:<br>
            <a href="{manage_link}">내 정보 관리하기</a></p>
            <p>감사합니다.</p>
            """,
        )
    # ── email 관련 End ──

    if req.notify_enabled:
        return {
            "message": "구독 신청이 완료되었습니다. 이메일을 확인해주세요.",
        }
    else:
        return {
            "message": "알림 없이 정보만 저장되었습니다. 나중에 알림을 받고 싶으시면 아래 링크에서 켜실 수 있어요.",
            "manage_link": manage_link,
        }

@app.get("/manage/{token}")
def get_subscriber_info(token: str, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.manage_token == token).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="유효하지 않은 링크입니다.")

    return {
        "email": subscriber.email,
        "calendar_type": subscriber.calendar_type,
        "birth_year": subscriber.birth_year,
        "birth_month": subscriber.birth_month,
        "birth_day": subscriber.birth_day,
        "birth_hour": subscriber.birth_hour,
        "birth_minute": subscriber.birth_minute,
        "gender": subscriber.gender,
        "notify_time": subscriber.notify_time,
        "notify_enabled": subscriber.notify_enabled,
    }

@app.patch("/manage/{token}")
def update_subscriber_info(token: str, req: UpdateSubscriberRequest, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.manage_token == token).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="유효하지 않은 링크입니다.")

    if req.calendar_type is not None:
        subscriber.calendar_type = req.calendar_type
    if req.year is not None:
        subscriber.birth_year = req.year
    if req.month is not None:
        subscriber.birth_month = req.month
    if req.day is not None:
        subscriber.birth_day = req.day
    if req.hour is not None:
        subscriber.birth_hour = req.hour
    if req.minute is not None:
        subscriber.birth_minute = req.minute
    if req.gender is not None:
        subscriber.gender = req.gender
    if req.notify_time is not None:
        subscriber.notify_time = req.notify_time

    db.commit()
    db.refresh(subscriber)

    manage_link = f"{os.getenv('BASE_URL')}/manage/{token}"

    send_email(
        to_email=subscriber.email,
        subject="[Kiwoon] 정보가 수정되었습니다",
        html_body=f"""
        <p>안녕하세요, Kiwoon입니다.</p>
        <p>아래와 같이 정보가 정상적으로 수정되었습니다.</p>
        <ul>
            <li>생년월일: {subscriber.calendar_type} {subscriber.birth_year}-{subscriber.birth_month:02d}-{subscriber.birth_day:02d}</li>
            <li>태어난 시간: {subscriber.birth_hour:02d}:{subscriber.birth_minute:02d}</li>
            <li>성별: {subscriber.gender}</li>
            <li>알림 시간: {subscriber.notify_time}</li>
            <li>알림 상태: {"켜짐" if subscriber.notify_enabled else "꺼짐"}</li>
        </ul>
        <p>내 정보 수정 및 알림 끄기는 아래 링크에서 가능합니다:<br>
        <a href="{manage_link}">내 정보 관리하기</a></p>
        <p>감사합니다.</p>
        """,
    )

    return {
        "message": "정보가 수정되었습니다.",
        "email": subscriber.email,
        "calendar_type": subscriber.calendar_type,
        "birth_year": subscriber.birth_year,
        "birth_month": subscriber.birth_month,
        "birth_day": subscriber.birth_day,
        "birth_hour": subscriber.birth_hour,
        "birth_minute": subscriber.birth_minute,
        "gender": subscriber.gender,
        "notify_time": subscriber.notify_time,
        "notify_enabled": subscriber.notify_enabled,
    }

@app.patch("/manage/{token}/notify")
def toggle_notify(token: str, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.manage_token == token).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="유효하지 않은 링크입니다.")

    subscriber.notify_enabled = not subscriber.notify_enabled
    db.commit()
    db.refresh(subscriber)

    manage_link = f"{os.getenv('BASE_URL')}/manage/{token}"
    status_text = "켜짐" if subscriber.notify_enabled else "꺼짐"

    send_email(
        to_email=subscriber.email,
        subject=f"[Kiwoon] 알림이 {status_text}으로 변경되었습니다",
        html_body=f"""
        <p>안녕하세요, Kiwoon입니다.</p>
        <p>알림 상태가 <b>{status_text}</b>으로 변경되었습니다.</p>
        <p>내 정보 수정 및 알림 설정은 아래 링크에서 가능합니다:<br>
        <a href="{manage_link}">내 정보 관리하기</a></p>
        <p>감사합니다.</p>
        """,
    )

    return {
        "message": f"알림이 {status_text}으로 변경되었습니다.",
        "notify_enabled": subscriber.notify_enabled,
    }

@app.post("/manage/resend-link")
def resend_manage_link(req: ResendLinkRequest, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.email == req.email).first()

    if subscriber:
        manage_link = f"{os.getenv('BASE_URL')}/manage/{subscriber.manage_token}"

        send_email(
            to_email=subscriber.email,
            subject="[Kiwoon] 관리 링크를 다시 보내드립니다",
            html_body=f"""
            <p>안녕하세요, Kiwoon입니다.</p>
            <p>요청하신 관리 링크입니다:</p>
            <p><a href="{manage_link}">내 정보 관리하기</a></p>
            <p>감사합니다.</p>
            """,
        )

    return {
        "message": "해당 이메일로 등록된 계정이 있다면, 관리 링크를 보내드렸습니다.",
    }