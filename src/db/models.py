"""
subscribers 테이블 모델.
- 알림 신청자의 이메일, 생년월일시, 알림 설정, 관리 토큰을 저장.
- 비밀번호 없음 (로그인 없는 '관리 링크' 방식 — manage_token으로 본인 확인).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from src.db.database import Base


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)

    calendar_type = Column(String, nullable=False)   # "양력" 또는 "음력"
    birth_year = Column(Integer, nullable=False)
    birth_month = Column(Integer, nullable=False)
    birth_day = Column(Integer, nullable=False)
    birth_hour = Column(Integer, nullable=True)  # None이면 생시 모름 (calculator.py hour_known=False와 동일 개념)
    birth_minute = Column(Integer, default=0)
    gender = Column(String, nullable=False)          # "남성" 또는 "여성"

    # ── 날씨 관련 ──
    region_1 = Column(String, nullable=False)   # 시/도 (예: "서울특별시")
    region_2 = Column(String, nullable=False)   # 구/군 (예: "강남구")


    notify_time = Column(String, nullable=False)      # 예: "07:30"
    notify_enabled = Column(Boolean, default=True)

    manage_token = Column(String, unique=True, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())