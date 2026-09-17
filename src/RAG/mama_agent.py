import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


load_dotenv()

ENDPOINT = os.getenv("AZURE_FOUNDRY_ENDPOINT")
AGENT_NAME = os.getenv("MAMA_AGENT_NAME")
AGENT_VERSION = os.getenv("MAMA_AGENT_VERSION")


def ask_mama(question: str) -> str:
    """
    사용자 질문을 MAMA RAG Agent에 전달하고
    텍스트 답변을 반환한다.
    """

    if not ENDPOINT or not AGENT_NAME or not AGENT_VERSION:
        raise ValueError(
            "Azure Foundry 환경변수가 설정되지 않았습니다."
        )

    if not question or not question.strip():
        raise ValueError(
            "질문이 비어 있습니다."
        )

    project_client = AIProjectClient(
        endpoint=ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    openai_client = project_client.get_openai_client()

    response = openai_client.responses.create(
        input=[
            {
                "role": "user",
                "content": question.strip(),
            }
        ],
        extra_body={
            "agent_reference": {
                "name": AGENT_NAME,
                "version": AGENT_VERSION,
                "type": "agent_reference",
            }
        },
    )

    return response.output_text