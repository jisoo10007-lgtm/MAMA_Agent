# =========================================================
# MAMA Agent Healthcheck Validator
#
# X_exam 기준
#
# 주의:
# 아래 range는 임상 진단 기준이 아니라
# OCR / 파싱 오류를 탐지하기 위한 sanity range이다.
# =========================================================


# =========================================================
# 숫자형 필드 범위 검증
# =========================================================

def validate_range(field, value):

    if value is None:
        return False, "값 없음"

    ranges = {

        # -------------------------------------------------
        # 신체계측
        # -------------------------------------------------
        "height_cm": (100, 220),
        "weight_kg": (30, 250),
        "waist_cm": (40, 200),
        "bmi_kg_m2": (10, 80),

        # -------------------------------------------------
        # 혈압
        # -------------------------------------------------
        "systolic_bp_mmhg": (60, 250),
        "diastolic_bp_mmhg": (30, 150),

        # -------------------------------------------------
        # 혈액
        # -------------------------------------------------
        "health_exam_hemoglobin_g_dl": (5, 25),

        # -------------------------------------------------
        # 염증
        # -------------------------------------------------
        "hs_crp_mg_l": (0, 100),

        # -------------------------------------------------
        # 당대사
        # -------------------------------------------------
        "fasting_glucose_mg_dl": (30, 500),
        "hba1c_pct": (2, 20),

        # -------------------------------------------------
        # 지질
        # -------------------------------------------------
        "total_cholesterol_mg_dl": (50, 500),
        "hdl_cholesterol_mg_dl": (10, 150),
        "triglycerides_mg_dl": (20, 1500),
        "ldl_cholesterol_mg_dl": (10, 400),

        # -------------------------------------------------
        # 간기능
        # -------------------------------------------------
        "ast_u_l": (0, 2000),
        "alt_u_l": (0, 2000),
        "ggt_u_l": (0, 2000),

        # -------------------------------------------------
        # 단백뇨
        #
        # X_exam에서는 DOUBLE 값
        # 현재 확인된 데이터 범위: 0 ~ 2
        # -------------------------------------------------
        "urine_protein_dipstick": (0, 2),

        # -------------------------------------------------
        # 철대사
        # -------------------------------------------------
        "ferritin_ng_ml": (0, 2000),

        # -------------------------------------------------
        # 신장기능
        # -------------------------------------------------
        "creatinine_mg_dl": (0.1, 20),

        # -------------------------------------------------
        # 영양
        # -------------------------------------------------
        "serum_folate_ng_ml": (0.1, 100),

        # -------------------------------------------------
        # 임신주수
        #
        # X_exam: gestational_age_days
        # OCR 오류 탐지를 위한 넓은 sanity range
        # -------------------------------------------------
        "gestational_age_days": (0, 320),

        # -------------------------------------------------
        # 체온
        # -------------------------------------------------
        "body_temperature_c": (30, 45),
    }

    # 정의되지 않은 필드는 범위 검증 생략
    if field not in ranges:
        return True, None

    # 숫자가 아닌 값
    if not isinstance(
        value,
        (int, float)
    ):
        return (
            False,
            f"숫자형 값이 아님: {value}"
        )

    min_value, max_value = ranges[field]

    if min_value <= value <= max_value:
        return True, None

    return (
        False,
        f"sanity range 벗어남: {value} "
        f"(허용 {min_value} ~ {max_value})"
    )


# =========================================================
# BMI 계산
# =========================================================

def calculate_bmi(
    height_cm,
    weight_kg
):

    if (
        height_cm is None
        or weight_kg is None
    ):
        return None

    if (
        not isinstance(
            height_cm,
            (int, float)
        )
        or not isinstance(
            weight_kg,
            (int, float)
        )
    ):
        return None

    if (
        height_cm <= 0
        or weight_kg <= 0
    ):
        return None

    height_m = (
        height_cm / 100
    )

    bmi = (
        weight_kg
        / (height_m ** 2)
    )

    return round(
        bmi,
        2
    )


# =========================================================
# 값 가져오기
# =========================================================

def get_value(
    data,
    field
):

    item = data.get(
        field
    )

    if item is None:
        return None

    if isinstance(
        item,
        dict
    ):
        return item.get(
            "value"
        )

    return item


# =========================================================
# X_exam 특수 필드 검증
# =========================================================

def validate_special_fields(
    data
):

    errors = []

    # -------------------------------------------------
    # 단백뇨
    # X_exam에서는 숫자형
    # -------------------------------------------------

    protein = get_value(
        data,
        "urine_protein_dipstick"
    )

    if protein is not None:

        if not isinstance(
            protein,
            (int, float)
        ):

            errors.append({
                "field":
                    "urine_protein_dipstick",

                "value":
                    protein,

                "message":
                    "단백뇨 값은 숫자형이어야 합니다."
            })

    # -------------------------------------------------
    # gestational_age_days
    # -------------------------------------------------

    gestational_days = get_value(
        data,
        "gestational_age_days"
    )

    if gestational_days is not None:

        if not isinstance(
            gestational_days,
            (int, float)
        ):

            errors.append({
                "field":
                    "gestational_age_days",

                "value":
                    gestational_days,

                "message":
                    "임신주수 일수는 숫자형이어야 합니다."
            })

    return errors


# =========================================================
# Cross-field 검증
# =========================================================

def validate_cross_fields(
    data
):

    errors = []

    # -------------------------------------------------
    # 혈압
    # 수축기 > 이완기
    # -------------------------------------------------

    sbp = get_value(
        data,
        "systolic_bp_mmhg"
    )

    dbp = get_value(
        data,
        "diastolic_bp_mmhg"
    )

    if (
        sbp is not None
        and dbp is not None
    ):

        if sbp <= dbp:

            errors.append({
                "field":
                    "blood_pressure",

                "value": {
                    "systolic": sbp,
                    "diastolic": dbp
                },

                "message":
                    "수축기혈압은 이완기혈압보다 커야 합니다."
            })

    # -------------------------------------------------
    # BMI 원문값 vs 계산값
    # -------------------------------------------------

    bmi_item = data.get(
        "bmi_kg_m2"
    )

    if isinstance(
        bmi_item,
        dict
    ):

        original_bmi = bmi_item.get(
            "value"
        )

        calculated_bmi = bmi_item.get(
            "calculated_value"
        )

        if (
            isinstance(
                original_bmi,
                (int, float)
            )
            and isinstance(
                calculated_bmi,
                (int, float)
            )
        ):

            difference = abs(
                original_bmi
                - calculated_bmi
            )

            # OCR 오류 탐지를 위한 비교
            # 진단 기준이 아님
            if difference > 1.0:

                errors.append({
                    "field":
                        "bmi_kg_m2",

                    "value": {
                        "original":
                            original_bmi,

                        "calculated":
                            calculated_bmi
                    },

                    "message":
                        "PDF BMI와 계산 BMI의 차이가 큽니다."
                })

    return errors


# =========================================================
# Pregnancy Metadata 검증
#
# 기존 azure_layout.py와의 호환을 위해 유지
# =========================================================

def validate_pregnancy_info(
    pregnancy_info
):

    errors = []

    if not pregnancy_info:
        return errors

    status = pregnancy_info.get(
        "status"
    )

    weeks = pregnancy_info.get(
        "gestational_weeks"
    )

    # -------------------------------------------------
    # 비임신인데 임신주수가 존재하는 경우
    # -------------------------------------------------

    if (
        status == "not_pregnant"
        and weeks is not None
    ):

        errors.append({
            "field":
                "pregnancy_info",

            "value": {
                "status": status,
                "gestational_weeks": weeks
            },

            "message":
                "비임신 상태에서는 임신주수가 없어야 합니다."
        })

    # -------------------------------------------------
    # 기존 pregnancy_info 주수 sanity check
    # -------------------------------------------------

    if (
        status == "pregnant"
        and weeks is not None
    ):

        if not isinstance(
            weeks,
            int
        ):

            errors.append({
                "field":
                    "gestational_weeks",

                "value":
                    weeks,

                "message":
                    "임신주수는 정수여야 합니다."
            })

        elif not (
            0 <= weeks <= 45
        ):

            errors.append({
                "field":
                    "gestational_weeks",

                "value":
                    weeks,

                "message":
                    "임신주수 sanity range를 벗어났습니다."
            })

    return errors


# =========================================================
# 전체 Healthcheck 검증
# =========================================================

def validate_healthcheck(
    data
):

    validation_errors = []

    # -------------------------------------------------
    # 숫자 범위
    # -------------------------------------------------

    for field, item in data.items():

        if not isinstance(
            item,
            dict
        ):
            continue

        value = item.get(
            "value"
        )

        valid, message = validate_range(
            field,
            value
        )

        if not valid:

            validation_errors.append({
                "field":
                    field,

                "value":
                    value,

                "message":
                    message
            })

    # -------------------------------------------------
    # 특수 필드
    # -------------------------------------------------

    special_errors = (
        validate_special_fields(
            data
        )
    )

    validation_errors.extend(
        special_errors
    )

    # -------------------------------------------------
    # Cross-field
    # -------------------------------------------------

    cross_errors = (
        validate_cross_fields(
            data
        )
    )

    validation_errors.extend(
        cross_errors
    )

    return validation_errors