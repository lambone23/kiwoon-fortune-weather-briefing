"""
기상청 API 생존 확인용 임시 테스트 스크립트.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

now = datetime.now()
if now.hour < 5:
    now = now - timedelta(days=1)
base_date = now.strftime("%Y%m%d")

params = {
    "ServiceKey": API_KEY,
    "pageNo": "1",
    "numOfRows": "10",
    "dataType": "JSON",
    "base_date": base_date,
    "base_time": "0500",
    "nx": "60",
    "ny": "127",
}

response = requests.get(URL, params=params)
print("상태 코드:", response.status_code)
print("응답 내용:")
print(response.text[:1000])