
# Kiwoon (기운)
 
AI(LLM) 사주 해석 기반 오늘의 운세 & 날씨 브리핑 서비스
 
氣(기상의 기) + 運(운세의 운) — 날씨와 운세, 두 정보를 하나로 묶어 전한다는 의미를 담았습니다.
 
매일 아침, 사주 계산 결과를 LLM이 해석하고 오늘의 날씨와 함께 이메일로 자동 발송합니다.
 
---
 
## 프로젝트 개요
 
- 사주 계산은 검증된 라이브러리(sajupy)가 담당하고, LLM은 그 계산 결과를 해석·서술하는 역할만 수행합니다.
- 계산과 해석의 책임을 분리해, LLM이 사주 원국을 임의로 추측하지 않도록 설계했습니다.
- 계산 로직의 정확도는 신한은행 '오늘의 운세'를 참고 샘플로 삼아 실측 대조했습니다.
- 사주 해석의 일관성과 신뢰도는 LLM Judge(Tier 1 형식·계산값 자동 채점 + Tier 2 회차 간 일관성 정성 평가)로 반복 검증했습니다.
- 개발 원칙은 하나였습니다. 비용 없이 개발하고, 비용 없이 운영하기.
---
 
## 배포
 
| 항목 | 내용 |
|---|---|
| 서비스 URL | https://kiwoon-fortune-weather-briefing.vercel.app/ |
| 프론트엔드 | Vercel |
| 백엔드 | Render |
 
<p align="center">
  <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https://kiwoon-fortune-weather-briefing.vercel.app/" alt="Kiwoon 서비스 QR 코드" width="180" />
</p>
---
 
## 주요 기능
 
- **비로그인 즉시 조회**: 가입 없이 생년월일시와 지역만 입력하면 오늘의 운세와 날씨를 바로 확인
- **알림 신청**: 이메일 등록으로 매일 설정한 시각에 자동 브리핑 수신
- **로그인 없는 정보 관리**: 비밀번호 없이 관리 링크(토큰) 기반으로 본인 확인 후 정보 수정·알림 On/Off·탈퇴 처리
- **생시 모름 지원**: 태어난 시각을 모르는 사용자도 조회 가능 (시주 관련 계산·해석은 자동 제외)
- **지역 무관 날씨 엔진**: 시/도·구/군 선택만으로 기상청 격자 좌표를 자동 변환해 조회
- **시간대별 날씨 조합**: 6시간 이내는 초단기예보, 그 이후는 단기예보로 조합해 정확도 확보
- **카드형 이메일 디자인**: 텍스트 기반 HTML로 구성해 이미지 없이도 웹과 동일한 톤 유지
---
 
## 기술 스택
 
| 영역 | 기술 |
|---|---|
| 프론트엔드 | Next.js 16 (App Router) · TypeScript |
| 백엔드 | FastAPI + uvicorn · SQLAlchemy (DB ORM) |
| DB | NeonDB (PostgreSQL) |
| AI / LLM | gpt-5-mini |
| 외부 API | 기상청 (단기예보 · 초단기예보) · Brevo (이메일) |
| 배포 | Vercel (프론트) · Render (백엔드) |
| 스케줄링 | cron-job.org |
 
---
 
## 시스템 구조
 
```
사용자 (브라우저)
        │
        ▼
Vercel · Next.js  ── 화면 4개 (조회 · 신청 · 관리)
        │  API 요청
        ▼
Render · FastAPI  ── 사주 계산 · 요청 처리 · 발송 로직
        │
        ├── NeonDB (구독 정보)
        ├── 기상청 API (날씨 조회)
        ├── LLM API (사주 해석)
        └── Brevo API (이메일 발송)
        ▲
        │ 매 분 호출
cron-job.org  ── 매일 정해진 시각에 Render를 깨워 브리핑 실행
```
 
### 폴더 구조
 
```
Kiwoon/
├── src/
│   ├── saju/
│   │   └── calculator.py        # 사주 계산 엔진 (sajupy 래핑)
│   ├── llm/
│   │   ├── prompts.py           # 운세 해석 프롬프트
│   │   └── fortune_generator.py # LLM 호출 로직
│   ├── weather/
│   │   ├── weather_fetcher.py   # 날씨 조회 엔진 (좌표 기반)
│   │   └── region_lookup.py     # 지역명 → 좌표 변환
│   ├── db/
│   │   ├── database.py
│   │   └── models.py            # subscribers 테이블
│   ├── notify/
│   │   └── email_sender.py      # 이메일 발송
│   ├── scheduler/
│   │   └── daily_job.py         # 매일 브리핑 발송 로직
│   └── api.py                   # FastAPI 엔드포인트
└── frontend/
    ├── lib/
    │   ├── api.ts                # 백엔드 API 호출 함수 모음
    │   └── styles/                # 공통 테마·스타일 토큰
    ├── components/                # 공통 UI 컴포넌트
    └── app/
        ├── page.tsx               # 진입 선택 화면
        ├── preview/                # 비로그인 조회 화면
        ├── subscribe/              # 알림 신청 화면
        └── manage/[token]/         # 정보 관리 화면
```
 
**subscribers 테이블**: 로그인 없이 `manage_token`으로 본인 확인. 사주 정보와 태어난 시각은 `birth_hour`를 nullable로 두어 "생시 모름"을 지원.
 
---
 
## 설치 및 실행 방법
 
### 백엔드
 
```bash
git clone https://github.com/lambone23/kiwoon-fortune-weather-briefing.git
cd kiwoon-fortune-weather-briefing
 
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
 
pip install -r requirements.txt
```
 
`.env.example`을 참고해 `.env` 파일을 생성한 뒤, 아래 명령으로 서버를 실행합니다.
 
```bash
uvicorn src.api:app --reload
```
 
### 프론트엔드
 
```bash
cd frontend
npm install
```
 
`frontend/.env.example`을 참고해 `.env.local`을 생성한 뒤 실행합니다.
 
```bash
npm run dev
```
 
두 서버가 모두 실행 중이어야 정상 동작합니다. 기본 접속 주소는 `http://localhost:3000`입니다.
 
---
 
## 개발 과정 기록
 
각 단계별 상세 작업 기록과 문제 해결 사례는 기술 블로그에 정리되어 있습니다.
 
[기술 블로그 바로가기](https://lambone.tistory.com/category/AI%20Agent%20%EC%97%94%EC%A7%80%EB%8B%88%EC%96%B4%20%EA%B3%BC%EC%A0%95)
 
---
 
## 문의
 
이메일: lambone234567@gmail.com
 
