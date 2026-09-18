import json
import os
from typing import Any

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from src.RAG.rag_policy import evaluate_rag_policy


load_dotenv()

ENDPOINT = os.getenv("AZURE_FOUNDRY_ENDPOINT")
AGENT_NAME = os.getenv("MAMA_AGENT_NAME")
AGENT_VERSION = os.getenv("MAMA_AGENT_VERSION")


def _build_user_input(
    question: str,
    context: dict[str, Any] | None = None,
) -> str:

    if context is None:
        return question.strip()

    # Context에 적용할 정책 결정
    policy = evaluate_rag_policy(context)

    context_json = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
    )

    policy_text = "\n".join(
        f"- {instruction}"
        for instruction in policy["instructions"]
    )

    return f"""
사용자 질문:
{question.strip()}

[STRUCTURED_CONTEXT]
{context_json}
[/STRUCTURED_CONTEXT]

[RAG_POLICY]
mode: {policy["mode"]}
abstain: {policy["abstain"]}
requires_clinician_review: {policy["requires_clinician_review"]}
patient_exposure_allowed: {policy["patient_exposure_allowed"]}

적용 규칙:
{policy_text}
[/RAG_POLICY]

반드시 위 STRUCTURED_CONTEXT와 RAG_POLICY를 따라 답변하세요.

추가 규칙:
- Context에 없는 환자 정보는 추정하거나 생성하지 마세요.
- ML이 계산한 결과를 RAG가 다시 계산하지 마세요.
- 의료적 설명이 필요한 경우 Agent에 연결된 승인된 근거 자료를 사용하세요.
- 근거가 없거나 Context와 근거가 충돌하면 추정하지 마세요.
- ABSTAIN 모드에서는 적용 불가 이유만 간결하게 설명하세요.
""".strip()

def ask_mama(
    question: str,
    context: dict[str, Any] | None = None,
) -> str:
    """
    사용자 질문과 선택적 구조화 Context를
    MAMA RAG Agent에 전달하고 답변을 반환한다.
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

    user_input = _build_user_input(
        question=question,
        context=context,
    )

    response = openai_client.responses.create(
        input=[
            {
                "role": "user",
                "content": user_input,
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