import os
from test.tts_test import speak_text

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

from RAG.mama_agent import ask_mama


load_dotenv()

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")


def recognize_speech() -> str | None:

    if not SPEECH_KEY or not SPEECH_REGION:
        raise ValueError(
            "AZURE_SPEECH_KEY 또는 AZURE_SPEECH_REGION이 .env에 없습니다."
        )

    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION,
    )

    speech_config.speech_recognition_language = "ko-KR"

    audio_config = speechsdk.audio.AudioConfig(
        use_default_microphone=True
    )

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    print("마이크에 질문해주세요...")

    result = speech_recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text

    if result.reason == speechsdk.ResultReason.NoMatch:
        print("음성을 인식하지 못했습니다.")
        return None

    if result.reason == speechsdk.ResultReason.Canceled:

        cancellation = result.cancellation_details

        print("음성 인식이 취소되었습니다.")
        print("이유:", cancellation.reason)

        if cancellation.reason == speechsdk.CancellationReason.Error:
            print("오류:", cancellation.error_details)

        return None

    return None


if __name__ == "__main__":

    print("=" * 50)
    print("MAMA Voice RAG Test")
    print("=" * 50)

    # 1. 음성 → 텍스트
    question = recognize_speech()

    if question:

        print("\n인식된 질문:")
        print(question)

        # 2. 텍스트 → MAMA RAG
        print("\nMAMA Agent에 질문 중...")

        answer = ask_mama(question)

        print("\nMAMA Agent 응답:")
        print(answer)

        # 3. RAG 답변 → 음성
        print("\nMAMA가 음성으로 답변합니다...")

        speak_text(answer)