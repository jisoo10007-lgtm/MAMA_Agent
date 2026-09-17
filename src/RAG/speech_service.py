import os

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk


load_dotenv()

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")


def _create_speech_config() -> speechsdk.SpeechConfig:
    """
    Azure Speech 설정을 생성한다.
    """

    if not SPEECH_KEY or not SPEECH_REGION:
        raise ValueError(
            "Azure Speech 환경변수가 설정되지 않았습니다."
        )

    return speechsdk.SpeechConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION,
    )


def recognize_speech() -> str | None:
    """
    기본 마이크의 한국어 음성을 텍스트로 변환한다.
    """

    speech_config = _create_speech_config()
    speech_config.speech_recognition_language = "ko-KR"

    audio_config = speechsdk.audio.AudioConfig(
        use_default_microphone=True
    )

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text

    if result.reason == speechsdk.ResultReason.NoMatch:
        return None

    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details

        if cancellation.reason == speechsdk.CancellationReason.Error:
            raise RuntimeError(
                f"Azure Speech STT 오류: "
                f"{cancellation.error_details}"
            )

        return None

    return None


def speak_text(text: str) -> bool:
    """
    텍스트를 한국어 음성으로 변환해 기본 스피커로 출력한다.
    """

    if not text or not text.strip():
        raise ValueError(
            "음성으로 변환할 텍스트가 비어 있습니다."
        )

    speech_config = _create_speech_config()

    speech_config.speech_synthesis_voice_name = (
        "ko-KR-SunHiNeural"
    )

    audio_config = speechsdk.audio.AudioOutputConfig(
        use_default_speaker=True
    )

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    result = synthesizer.speak_text_async(
        text.strip()
    ).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return True

    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details

        if cancellation.reason == speechsdk.CancellationReason.Error:
            raise RuntimeError(
                f"Azure Speech TTS 오류: "
                f"{cancellation.error_details}"
            )

    return False