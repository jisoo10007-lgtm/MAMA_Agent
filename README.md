# MAMA Agent

> 건강검진 PDF를 구조화하고, 여성 건강 정보를 RAG 기반으로 제공하는 AI
> 헬스케어 서비스

## 1. 프로젝트 개요

MAMA Agent는 건강검진 기록과 사용자 정보를 활용해 여성의 건강 상태를
이해하기 쉬운 형태로 제공하는 프로젝트입니다.

현재 개발 범위는 다음 세 가지입니다.

-   **OCR**: 건강검진 PDF → 구조화된 건강검진 JSON
-   **RAG**: 임신 전·임신 중·출산 후 여성 건강 관련 질의응답
-   **Voice**: 음성 질문 → STT → RAG → TTS

향후 Databricks의 ML 결과가 확정되면 질병 위험 예측과 Peer Comparison
결과를 RAG Context에 연결할 예정입니다.

> Peer Comparison은 질병 진단이나 발생 확률이 아니라 참조 집단 내 상대적
> 위치를 설명하기 위한 정보입니다.

------------------------------------------------------------------------

## 2. 현재 시스템 구조

``` text
[건강검진]
Health Check PDF
      ↓
Azure AI Document Intelligence
      ↓
Table Parsing / Field Mapping
      ↓
Validation
      ↓
Canonical Healthcheck JSON


[텍스트 질문]
User Question
      ↓
FastAPI /api/chat
      ↓
MAMA RAG (Azure Foundry)
      ↓
Text Answer


[음성 질문]
User Voice
      ↓
FastAPI /api/voice
      ↓
Azure Speech STT
      ↓
MAMA RAG
      ↓
Azure Speech TTS
      ↓
Text + Voice Answer


[추후 연동]
OCR / User Data
      ↓
Databricks / ML
      ↓
Risk Prediction / Peer Comparison
      ↓
RAG Context
      ↓
MAMA Explanation
```

------------------------------------------------------------------------

## 3. 주요 기능

### OCR

Azure AI Document Intelligence의 `prebuilt-layout`을 사용해 건강검진
PDF의 표 구조를 분석합니다.

``` text
PDF
 ↓
Document Intelligence
 ↓
Table Extraction
 ↓
Healthcheck Parser
 ↓
Field Mapping
 ↓
Validation
 ↓
Structured JSON
```

현재 고정 형식의 테스트 건강검진 PDF를 대상으로 OCR 파이프라인과 검증
로직을 구현했습니다.

### RAG

Azure Foundry 기반 MAMA Agent가 여성 건강 관련 문서를 검색하여
답변합니다.

주요 범위:

-   임신 준비
-   임신 중 건강관리
-   출산 후 건강관리
-   건강검진 수치 관련 설명

ML 결과가 전달되는 경우 RAG는 ML 결과를 다시 계산하지 않고 **전달받은
결과를 근거 문서와 함께 설명하는 역할**을 담당합니다.

### Voice

Azure Speech를 사용합니다.

``` text
Voice → STT → RAG → TTS → Voice
```

현재 로컬 마이크 테스트와 FastAPI 음성 API 테스트를 완료했습니다.

------------------------------------------------------------------------

## 4. FastAPI

### 실행

``` bash
uvicorn src.API.main:app --reload
```

-   Local API: `http://127.0.0.1:8000`
-   Swagger: `http://127.0.0.1:8000/docs`

### API 목록

  기능           Method   Endpoint       입력   출력
  -------------- -------- -------------- ------ --------------------
  텍스트 질문    POST     `/api/chat`    JSON   RAG 답변
  건강검진 OCR   POST     `/api/ocr`     PDF    OCR JSON
  음성 질문      POST     `/api/voice`   WAV    질문 + 답변 + 음성

### `/api/chat`

Request:

``` json
{
  "question": "임신 중 엽산은 왜 필요한가요?"
}
```

Response:

``` json
{
  "success": true,
  "data": {
    "answer": "임신 중 엽산은..."
  }
}
```

### `/api/ocr`

`multipart/form-data`

``` text
file: healthcheck.pdf
```

Response:

``` json
{
  "success": true,
  "data": {
    "filename": "healthcheck.pdf",
    "ocr_result": {}
  }
}
```

### `/api/voice`

현재 개발 버전에서는 WAV 입력을 지원합니다.

`multipart/form-data`

``` text
file: voice.wav
```

Response:

``` json
{
  "success": true,
  "data": {
    "question": "임신 중 엽산은 왜 필요한가요?",
    "answer": "임신 중 엽산은...",
    "audio_base64": "UklGR...",
    "audio_format": "wav"
  }
}
```

### 공통 오류 응답

``` json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "오류 메시지"
  }
}
```

로컬 프론트엔드 연동을 위한 CORS 설정도 적용되어 있습니다.

------------------------------------------------------------------------

## 5. 프로젝트 구조

``` text
MAMA_Agent/
├─ src/
│  ├─ API/
│  │  └─ main.py
│  ├─ OCR/
│  │  ├─ azure_layout.py
│  │  ├─ field_mapper.py
│  │  ├─ healthcheck_table_parser.py
│  │  ├─ patient_manager.py
│  │  └─ validator.py
│  └─ RAG/
│     ├─ mama_agent.py
│     ├─ rag_context.py
│     ├─ rag_policy.py
│     └─ speech_service.py
├─ tests/
├─ data/
├─ output/
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

------------------------------------------------------------------------

## 6. 기술 스택

  영역                 기술
  -------------------- --------------------------------
  Backend              Python, FastAPI, Uvicorn
  OCR                  Azure AI Document Intelligence
  RAG                  Azure Foundry
  Voice                Azure Speech
  Data / ML            pandas, NumPy, scikit-learn
  향후 데이터 플랫폼   Azure Databricks

------------------------------------------------------------------------

## 7. 환경 설정

### 가상환경

``` bash
python -m venv .venv
```

Windows:

``` bash
.venv\Scripts\activate
```

### 패키지 설치

``` bash
pip install -r requirements.txt
```

### 환경변수

`.env.example`을 참고하여 `.env`를 생성합니다.

``` env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=

AZURE_FOUNDRY_ENDPOINT=
MAMA_AGENT_NAME=
MAMA_AGENT_VERSION=

AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
```

`.env`에는 실제 인증 정보를 저장하며 Git에 커밋하지 않습니다.

------------------------------------------------------------------------

## 8. 개발 상태

### 완료

-   [x] Azure Document Intelligence Python SDK 연동
-   [x] Healthcheck Table Parser
-   [x] Field Mapping
-   [x] OCR Validation
-   [x] 고정 형식 테스트 PDF OCR 검증
-   [x] Azure Foundry RAG 연동
-   [x] RAG Context / Policy 구조
-   [x] Azure Speech STT
-   [x] Azure Speech TTS
-   [x] FastAPI `/api/chat`
-   [x] FastAPI `/api/ocr`
-   [x] FastAPI `/api/voice`
-   [x] CORS
-   [x] 공통 성공/오류 응답 형식

### 진행 예정

-   [ ] 실제 웹 프론트엔드 연동
-   [ ] 사용자 설문 데이터 연동
-   [ ] Databricks 데이터 저장/조회 연동
-   [ ] 실제 ML Risk Prediction 결과 연동
-   [ ] 실제 Peer Comparison 결과 연동
-   [ ] 배포 환경 구성

> 현재 ML/RAG 연동 테스트에 사용한 ML 값은 합성 테스트 데이터입니다.
> 실제 ML 및 Databricks 출력 인터페이스가 확정된 후 운영 연동을
> 진행합니다.

------------------------------------------------------------------------

## 9. Security

Azure API Key와 Endpoint 등 인증 정보는 `.env`에서 관리합니다.

`.gitignore` 예시:

``` gitignore
.env
.venv/
venv/
__pycache__/
*.pyc
output/
```

인증 정보가 포함된 `.env` 파일은 GitHub Repository에 업로드하지
않습니다.
