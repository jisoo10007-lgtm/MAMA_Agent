from typing import Any


def evaluate_rag_policy(
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    MOMI RAG 정책에 따라 Context의 답변 모드와
    안전 규칙을 결정한다.
    """

    if context is None:
        return {
            "mode": "GENERAL",
            "abstain": False,
            "requires_clinician_review": False,
            "patient_exposure_allowed": False,
            "instructions": [],
        }

    instructions = []
    requires_clinician_review = False

    data_quality = context.get("data_quality", {})
    peer_summary = context.get("peer_summary")
    risk_predictions = context.get("risk_predictions", [])
    health_exam_signals = context.get("health_exam_signals", [])

    # --------------------------------------------------
    # 1. 합성 데이터
    # --------------------------------------------------

    if context.get("is_synthetic") is True:
        instructions.append(
            "이 Context는 합성 데이터입니다. "
            "시뮬레이션 예시로만 설명하고 실제 환자 판단에 사용하지 마세요."
        )

    # --------------------------------------------------
    # 2. 명시적 ABSTAIN
    # --------------------------------------------------

    abstention_reason = data_quality.get("abstention_reason")

    if abstention_reason:
        return {
            "mode": "ABSTAIN",
            "abstain": True,
            "requires_clinician_review": True,
            "patient_exposure_allowed": False,
            "instructions": instructions + [
                f"판단 보류 사유: {abstention_reason}",
                "근거가 부족하거나 적용할 수 없는 결과를 추정하지 마세요.",
                "존재하지 않는 수치, 순위, 증상 또는 진단을 생성하지 마세요.",
                "적용할 수 없는 이유만 간결하게 설명하세요.",
            ],
        }

    # --------------------------------------------------
    # 3. 임신부 PeerGroup 적용 차단
    # --------------------------------------------------

    if (
        context.get("life_stage") == "pregnant"
        and peer_summary is not None
        and peer_summary.get("reference_applicable") is False
    ):
        return {
            "mode": "ABSTAIN",
            "abstain": True,
            "requires_clinician_review": True,
            "patient_exposure_allowed": False,
            "instructions": instructions + [
                "임신부에게 비임신 Reference Persona를 적용하지 마세요.",
                "Peer 순위나 백분위를 새로 계산하지 마세요.",
                "ABSTAIN_REFERENCE_NOT_APPLICABLE로 처리하세요.",
            ],
        }

    # --------------------------------------------------
    # 4. OCR 품질 검사
    # --------------------------------------------------

    invalid_ocr = [
        signal
        for signal in health_exam_signals
        if signal.get("quality_status")
        in {"needs_review", "conflict", "unknown"}
    ]

    if invalid_ocr:
        instructions.extend(
            [
                "검증되지 않았거나 충돌하는 OCR 값은 임상적으로 해석하지 마세요.",
                "해당 수치는 재검증이 필요하다고 설명하세요.",
            ]
        )

    # --------------------------------------------------
    # 5. 임신주수 미확인
    # --------------------------------------------------

    if (
        context.get("life_stage") == "pregnant"
        and context.get("gestational_age_days") is None
    ):
        instructions.append(
            "임신주수가 확인되지 않았으므로 "
            "주수 의존 기준이나 위험 해석은 보류하세요."
        )

    # --------------------------------------------------
    # 6. 질병 위험 ML
    # --------------------------------------------------

    if risk_predictions:

        for prediction in risk_predictions:
            review_status = prediction.get(
                "clinician_review_status"
            )

            if review_status in {
                "PENDING",
                "REJECTED",
                "OVERRIDDEN",
            }:
                requires_clinician_review = True

        instructions.extend(
            [
                "ML score를 질병 발생 확률이나 확진으로 표현하지 마세요.",
                "risk_band는 모델이 제공한 위험 분류 결과로만 설명하세요.",
                "raw_score 또는 내부 모델 근거를 환자에게 노출하지 마세요.",
                "input_coverage와 abstention_reason을 함께 고려하세요.",
                "Clinical Note 신호를 새로운 확진 Label로 변환하지 마세요.",
                "LOW_HB_NEXT_4W는 후속 Hb 상태 endpoint이며 "
                "철결핍 원인 진단이나 산후빈혈 진단으로 표현하지 마세요.",
            ]
        )

        return {
            "mode": "RISK",
            "abstain": False,
            "requires_clinician_review": (
                requires_clinician_review
            ),
            "patient_exposure_allowed": False,
            "instructions": instructions,
        }

    # --------------------------------------------------
    # 7. PeerGroup
    # --------------------------------------------------

    if peer_summary is not None:

        instructions.extend(
            [
                "PeerGroup 결과는 Reference 대비 상대적 위치로만 설명하세요.",
                "Persona 명칭을 진단명으로 표현하지 마세요.",
                "Peer percentile을 질병위험 또는 진단 확률로 변환하지 마세요.",
                "Peer percentile을 전체 건강 점수로 변환하지 마세요.",
                "clinical_diagnosis=false를 유지하세요.",
                "distance_to_center의 좋고 나쁨을 임의로 평가하지 마세요.",
            ]
        )

        return {
            "mode": "PEER",
            "abstain": False,
            "requires_clinician_review": False,
            "patient_exposure_allowed": False,
            "instructions": instructions,
        }

    # --------------------------------------------------
    # 8. 일반 RAG
    # --------------------------------------------------

    return {
        "mode": "GENERAL",
        "abstain": False,
        "requires_clinician_review": False,
        "patient_exposure_allowed": False,
        "instructions": instructions,
    }