"""
DB 연결 설정.
- .env의 DATABASE_URL을 읽어서 NeonDB(PostgreSQL) 연결 생성.
- pool_pre_ping=True: 커넥션 풀에서 연결을 꺼내 쓰기 직전에 가벼운 SELECT 1을
  실행해 "이 연결이 아직 살아있는지" 먼저 확인함. NeonDB는 일정 시간 요청이
  없으면 컴퓨트가 절전 상태로 들어가며 기존 커넥션을 서버 쪽에서 끊어버리는데,
  이 옵션이 없으면 SQLAlchemy가 죽은 연결을 그대로 재사용하려다
  "server closed the connection unexpectedly" 에러가 남 (Part6 스케줄러
  로그에서 실제 확인된 문제).
- pool_recycle=280: 커넥션을 280초(약 4분 40초)마다 강제로 새로 맺음.
  NeonDB의 절전 전환 주기보다 짧게 잡아, 애초에 오래 방치되는 연결
  자체를 줄임 (pool_pre_ping과 이중 안전장치).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()