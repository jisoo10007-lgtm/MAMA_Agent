import os
import tempfile
import base64
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Request,
)
from pydantic import BaseModel

from src.RAG.mama_agent import ask_mama
from src.OCR.azure_layout import process_healthcheck

from src.RAG.speech_service import (
    recognize_audio_file,
    synthesize_speech_to_file,
)


app = FastAPI(
    title="MAMA Agent API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def error_response(
    code: str,
    message: str,
    status_code: int,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    if exc.status_code == 400:
        code = "BAD_REQUEST"

    elif exc.status_code == 404:
        code = "NOT_FOUND"

    else:
        code = "HTTP_ERROR"

    return error_response(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code,
    )

@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    print(f"[SERVER ERROR] {exc}")

    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="서버 처리 중 오류가 발생했습니다.",
        status_code=500,
    )

class ChatRequest(BaseModel):
    question: str


def remove_temp_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

@app.get("/")
def root():
    return {
        "service": "MAMA Agent API",
        "status": "running",
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        answer = ask_mama(
            question=request.question,
        )

        return {
            "success": True,
            "data": {
                "answer": answer,
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="MAMA Agent 처리 중 오류가 발생했습니다.",
        )

@app.post("/api/ocr")
async def ocr_healthcheck(
    file: UploadFile = File(...)
):
    # PDF 파일인지 확인
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="파일명이 없습니다.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="PDF 파일만 업로드할 수 있습니다.",
        )

    temp_path = None

    try:
        # 업로드된 PDF 읽기
        pdf_bytes = await file.read()

        if not pdf_bytes:
            raise HTTPException(
                status_code=400,
                detail="업로드된 PDF가 비어 있습니다.",
            )

        # 기존 OCR 함수가 파일 경로를 사용하므로
        # 임시 PDF 파일 생성
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name

        # 기존 OCR 실행
        result = process_healthcheck(temp_path)

        return {
            "success": True,
            "data": {
                "patient_id": result["patient_id"],
                "filename": file.filename,
                "ocr_result": {
                    key: value
                    for key, value in result.items()
                    if key != "storage"
                },
                "storage": result["storage"],
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR 처리 중 오류가 발생했습니다: {str(e)}",
        )

    finally:
        # OCR이 끝나면 서버의 임시 PDF 삭제
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/voice")
async def voice_chat(
    file: UploadFile = File(...)
):
    input_path = None
    output_path = None

    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="음성 파일명이 없습니다.",
            )

        if not file.filename.lower().endswith(".wav"):
            raise HTTPException(
                status_code=400,
                detail="현재 음성 테스트는 WAV 파일만 지원합니다.",
            )

        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="업로드된 음성 파일이 비어 있습니다.",
            )

        # 1. 업로드된 음성을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
        ) as input_file:
            input_file.write(audio_bytes)
            input_path = input_file.name

        # 2. STT
        question = recognize_audio_file(
            input_path
        )

        if not question:
            raise HTTPException(
                status_code=400,
                detail="음성을 인식하지 못했습니다.",
            )

        # 3. RAG
        answer = ask_mama(
            question=question,
        )

        # 4. TTS용 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
        ) as output_file:
            output_path = output_file.name

        synthesize_speech_to_file(
            text=answer,
            output_path=output_path,
        )

        # 5. 생성된 WAV 읽기
        with open(output_path, "rb") as audio_file:
            answer_audio = audio_file.read()

        # 6. WAV → Base64
        audio_base64 = base64.b64encode(
            answer_audio
        ).decode("utf-8")

        # 7. 웹에 JSON 반환
        return {
            "success": True,
            "data": {
                "question": question,
                "answer": answer,
                "audio_base64": audio_base64,
                "audio_format": "wav",
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"음성 처리 중 오류가 발생했습니다: {str(e)}",
        )

    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)

        if output_path and os.path.exists(output_path):
            os.remove(output_path)