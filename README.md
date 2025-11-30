# Discord Ticket Bot

이 프로젝트는 Discord.py, Quart(Flask와 호환되며 asyncio 기반 비동기 처리를 지원하는 Python ASGI 웹 프레임워크)를 사용하는 **디스코드 티켓봇**입니다.
현재 **Beta** 상태로, 일부 기능이 불안정하거나 작동하지 않을 수 있습니다.

---

## 설치 및 환경 설정

### 1. 가상환경 생성 및 활성화

```
# 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. 의존성 설치

```
pip install -r requirements.txt
```

### 3. 환경 변수 설정

1. `.env.example` 파일을 `.env`로 복사

```
# macOS / Linux
cp .env.example .env

# Windows
copy .env.example .env
```

2. `.env` 파일을 열고 필요한 값을 작성


> ⚠️ `.env` 파일은 절대 외부에 공개하지 마세요.

### 4. 실행

최초 실행 시 config.ini가 생성되며 프로그램이 종료됩니다. config.ini 설정 후 다시 실행해주세요.
```
python3 src/index.py
```
---

## 사용권 및 라이선스
- **서비스 운영 중:** AGPL 라이선스 적용  
  - 배포, 서비스 제공, 코드 수정 등 일체의 행위에 대해 **소스코드 공개 의무**가 발생합니다.

이 프로젝트는 [DiscordChatExporterPy](https://github.com/mahtoid/DiscordChatExporterPy) 라이브러리를 수정한 소스를 사용하고 있습니다.
- `chat_exporter` 모듈: 한글화 및 후원 문구 제거 목적 일부 수정
- `static/css/style.css`: 수정 없음, 프로젝트에서 base HTML 스타일 오버라이드 목적

> ⚠️ 현재 프로젝트는 개발 중이며, 현재 Beta 버전인 상태로 아직 기능이 작동하지 않거나 불안정할 수 있습니다.
