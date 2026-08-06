"""
FastAPI 서버 진입점.
- main.py와 동일한 로직(계산→해석)을 웹 요청(JSON)으로 처리.
- calculator.py, prompts.py, fortune_generator.py는 수정 없이 그대로 재사용.
"""

from fastapi.middleware.cors import CORSMiddleware

import os
from src.notify.email_sender import send_email, build_notification_email
from src.weather.region_lookup import get_all_region_1, get_region_2_list
from src.weather.weather_fetcher import get_weather_by_region, format_weather_summary

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_fortunes, "cron", minute="*")

@app.get("/regions")
def get_regions():
    return {"regions": get_all_region_1()}

@app.get("/regions/{region_1}")
def get_sub_regions(region_1: str):
    return {"region_2_list": get_region_2_list(region_1)}

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
    region_1: str   # 시/도
    region_2: str   # 구/군

class SubscribeRequest(BaseModel):
    email: str
    calendar_type: str
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str
    region_1: str   # 시/도 (예: "서울특별시")
    region_2: str   # 구/군 (예: "강남구")
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
    region_1: Optional[str] = None
    region_2: Optional[str] = None
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

    weather_summary = get_weather_by_region(req.region_1, req.region_2)
    weather_text = format_weather_summary(weather_summary)

    return {
        "saju_summary": summary,
        "fortune": fortune_text,
        "weather": weather_text,
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
        region_1=req.region_1,
        region_2=req.region_2,
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
            html_body=build_notification_email(
                icon="✅",
                title="신청이 완료되었어요",
                message_lines=[
                    f"매일 <b>{req.notify_time}</b>에 오늘의 운세 브리핑을 보내드릴게요.",
                    f"날씨 지역: {req.region_1} {req.region_2}",
                ],
                manage_link=manage_link,
                accent_color="#3aa66b",   # 완료 화면의 초록과 동일 톤
            ),
        )
    # ── email 관련 End ──

    return {
        "message": (
            "구독 신청이 완료되었습니다. 이메일을 확인해주세요."
            if req.notify_enabled
            else "알림 없이 정보만 저장되었습니다. 나중에 알림을 받고 싶으시면 아래 링크에서 켜실 수 있어요."
        ),
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
        "region_1": subscriber.region_1,
        "region_2": subscriber.region_2,        
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
    if req.region_1 is not None:
        subscriber.region_1 = req.region_1
    if req.region_2 is not None:
        subscriber.region_2 = req.region_2        
    if req.notify_time is not None:
        subscriber.notify_time = req.notify_time

    db.commit()
    db.refresh(subscriber)

    manage_link = f"{os.getenv('BASE_URL')}/manage/{token}"

    send_email(
        to_email=subscriber.email,
        subject="[Kiwoon] 정보가 수정되었습니다",
        html_body=build_notification_email(
            icon="✏️",
            title="정보가 수정되었어요",
            message_lines=[
                f"생년월일: {subscriber.calendar_type} {subscriber.birth_year}-{subscriber.birth_month:02d}-{subscriber.birth_day:02d}",
                f"태어난 시간: {subscriber.birth_hour:02d}:{subscriber.birth_minute:02d} · 성별: {subscriber.gender}",
                f"날씨 지역: {subscriber.region_1} {subscriber.region_2}",
                f"알림 시간: {subscriber.notify_time} · 알림 상태: {'켜짐' if subscriber.notify_enabled else '꺼짐'}",
            ],
            manage_link=manage_link,
            accent_color="#4a90d9",
        ),
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
        "region_1": subscriber.region_1,
        "region_2": subscriber.region_2,        
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
        html_body=build_notification_email(
            icon="🔔" if subscriber.notify_enabled else "🔕",
            title=f"알림이 {status_text}으로 변경되었어요",
            message_lines=[
                f"매일 {subscriber.notify_time}에 브리핑을 받아보실 수 있어요." if subscriber.notify_enabled
                else "알림이 꺼져서 더 이상 브리핑 메일이 가지 않아요.",
            ],
            manage_link=manage_link,
            accent_color="#3aa66b" if subscriber.notify_enabled else "#c99a5a",
        ),
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
            <p>관리 링크는 본인 확인용 비밀 링크예요. 다른 사람에게 공유하지 마세요.</p>
            <p>감사합니다.</p>
            """,
        )

    return {
        "message": "해당 이메일로 등록된 계정이 있다면, 관리 링크를 보내드렸습니다.",
    }

@app.delete("/manage/{token}")
def delete_subscriber(token: str, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.manage_token == token).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="유효하지 않은 링크입니다.")

    email = subscriber.email
    db.delete(subscriber)
    db.commit()

    send_email(
        to_email=email,
        subject="[Kiwoon] 탈퇴가 완료되었습니다",
        html_body=f"""
        <meta name="color-scheme" content="dark light">
        <meta name="supported-color-schemes" content="dark light">
        <div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif; max-width:480px; margin:0 auto;">
            <div style="background-color:#3a3a37; padding:24px 16px; border-radius:14px;">
                <div style="text-align:center; margin-bottom:20px;">
                    <span style="font-size:20px; font-weight:700; color:#f5f3ee;">🌤️ KI WOON 기운 🔮</span>
                </div>
                <div style="border:1px solid #5a5955; border-radius:12px; overflow:hidden;">
                    <div style="background-color:#8a4a4a; padding:14px 16px;">
                        <span style="font-size:15px; font-weight:600; color:#ffffff;">👋 탈퇴가 완료되었어요</span>
                    </div>
                    <div style="background-color:#4d4c48; padding:18px 16px;">
                        <p style="margin:0; color:#e8e6e0; font-size:14px; line-height:1.6;">
                            요청하신 대로 탈퇴 처리가 완료되어, 등록하신 모든 정보가 삭제되었습니다.
                        </p>
                        <p style="margin:10px 0 0 0; color:#e8e6e0; font-size:14px; line-height:1.6;">
                            다시 이용하고 싶으시면 언제든 새로 신청해주세요.
                        </p>
                    </div>
                </div>
                <p style="text-align:center; font-size:11px; color:#6a6965; margin-top:20px;">
                    문의: lambone234567@gmail.com<br>
                    © 2026 Kiwoon. All rights reserved.
                </p>
            </div>
        </div>
        """,
    )

    return {"message": "탈퇴가 완료되었습니다. 그동안 이용해주셔서 감사합니다."}