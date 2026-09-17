import os

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk


load_dotenv()

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")


def speak_text(text: str):

    if not SPEECH_KEY or not SPEECH_REGION:
        raise ValueError(
            "AZURE_SPEECH_KEY 또는 AZURE_SPEECH_REGION이 .env에 없습니다."
        )

    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION,
    )

    # 한국어 여성 음성
    speech_config.speech_synthesis_voice_name = "ko-KR-SunHiNeural"

    # 기본 스피커로 출력
    audio_config = speechsdk.audio.AudioOutputConfig(
        use_default_speaker=True
    )

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    print("음성 출력 중...")

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("음성 출력 성공")

    elif result.reason == speechsdk.ResultReason.Canceled:

        cancellation = result.cancellation_details

        print("음성 출력 실패")
        print("이유:", cancellation.reason)

        if cancellation.reason == speechsdk.CancellationReason.Error:
            print("오류:", cancellation.error_details)


if __name__ == "__main__":

    text = (
        "안녕하세요. MAMA입니다. "
        "궁금한 여성 건강 정보를 편하게 물어보세요."
    )

    speak_text(text)