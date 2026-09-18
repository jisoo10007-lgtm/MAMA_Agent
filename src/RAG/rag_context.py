import uuid
from datetime import datetime, timezone
from typing import Any


VALID_LIFE_STAGES = {
    "pregnant",
    "nonpregnant",
    "postpartum",
    "unknown",
}


def create_rag_context(
    *,
    life_stage: str,
    risk_predictions: list[dict[str, Any]] | None = None,
    health_exam_signals: list[dict[str, Any]] | None = None,
    peer_summary: dict[str, Any] | None = None,
    clinical_note_signals: list[dict[str, Any]] | None = None,
    health_history_summary: list[dict[str, Any]] | None = None,
    data_quality: dict[str, Any] | None = None,
    patient_id_pseudonym: str | None = None,
    pregnancy_id_pseudonym: str | None = None,
    gestational_age_days: int | None = None,
    reference_eligibility: str = "unknown",
    is_synthetic: bool = False,
) -> dict[str, Any]:

    if life_stage not in VALID_LIFE_STAGES:
        raise ValueError(
            f"지원하지 않는 life_stage입니다: {life_stage}"
        )

    if gestational_age_days is not None:
        if not 0 <= gestational_age_days <= 315:
            raise ValueError(
                "gestational_age_days는 0~315 범위여야 합니다."
            )

    request_id = str(uuid.uuid4())
    context_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc).isoformat()

    context = {
        "request_id": request_id,
        "context_id": context_id,
        "patient_id_pseudonym": patient_id_pseudonym,
        "pregnancy_id_pseudonym": pregnancy_id_pseudonym,
        "as_of": now,
        "life_stage": life_stage,
        "gestational_age_days": gestational_age_days,
        "reference_eligibility": reference_eligibility,

        "risk_predictions": risk_predictions or [],

        "clinical_note_signals": clinical_note_signals or [],

        "health_exam_signals": health_exam_signals or [],

        "peer_summary": peer_summary,

        "health_history_summary": health_history_summary or [],

        "data_quality": data_quality or {
            "n_features_expected": 0,
            "n_features_present": 0,
            "missing_features": [],
            "conflicts": [],
            "stale_features": [],
            "abstention_reason": None,
        },

        "is_synthetic": is_synthetic,
    }

    return context