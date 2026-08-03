"""
기상청 API 생존 확인용 임시 테스트 스크립트.
- 2026-08 재발급받은 인증키/엔드포인트로 처음부터 검증.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import unquote

load_dotenv()

API_KEY = unquote(os.getenv("WEATHER_API_KEY"))
BASE_URL = os.getenv("WEATHER_BASE_URL")
URL = f"{BASE_URL}/getVilageFcst"

now = datetime.now()
if now.hour < 5:
    now = now - timedelta(days=1)
base_date = now.strftime("%Y%m%d")

params = {
    "serviceKey": API_KEY,   # 대소문자 주의: serviceKey (카멜케이스, 공식 문서 기준)
    "pageNo": "1",
    "numOfRows": "10",
    "dataType": "JSON",
    "base_date": base_date,
    "base_time": "0500",
    "nx": "60",   # 서울 중구 기준 (테스트용 고정값)
    "ny": "127",
}

response = requests.get(URL, params=params)
print("요청 URL:", response.url)
print("상태 코드:", response.status_code)
print("응답 내용:")
print(response.text[:1500])