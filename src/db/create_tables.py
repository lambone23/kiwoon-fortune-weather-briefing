"""
정의된 모델(Subscriber)을 바탕으로 실제 DB 테이블을 생성하는 일회성 스크립트.
"""

from src.db.database import engine, Base
from src.db.models import Subscriber

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료")