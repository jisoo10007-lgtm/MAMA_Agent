# =========================================================
# MAMA Agent Healthcheck Validator
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
        # 시력
        # -------------------------------------------------
        "vision_left": (0, 5),
        "vision_right": (0, 5),

        # -------------------------------------------------
        # 혈압
        # -------------------------------------------------
        "systolic_bp_mmhg": (60, 250),
        "diastolic_bp_mmhg": (30, 150),

        # -------------------------------------------------
        # 혈액
        # -------------------------------------------------
        "health_exam_hemoglobin_g_dl": (5, 25),
        "current_hemoglobin_g_dl": (5, 25),

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
        # 체온
        # -------------------------------------------------
        "body_temperature_c": (30, 45),
    }

    # 범위 검사가 필요 없는 category field 등
    if field not in ranges:
        return True, None

    # 숫자가 아닌 값이 들어온 경우
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
# Category Field 검증
# =========================================================

def validate_categories(
    data
):

    errors = []

    # -------------------------------------------------
    # 청력
    # -------------------------------------------------

    hearing_allowed = {
        "normal",
        "abnormal",
        "unknown"
    }

    for field in [
        "hearing_left",
        "hearing_right"
    ]:

        value = get_value(
            data,
            field
        )

        if (
            value is not None
            and value not in hearing_allowed
        ):

            errors.append({
                "field": field,
                "value": value,
                "message":
                    "허용되지 않은 청력 category"
            })

    # -------------------------------------------------
    # 단백뇨
    # -------------------------------------------------

    protein_allowed = {
        "negative",
        "trace",
        "1+",
        "2+",
        "3+",
        "4+",
        "unknown"
    }

    protein = get_value(
        data,
        "urine_protein_dipstick"
    )

    if (
        protein is not None
        and protein not in protein_allowed
    ):

        errors.append({
            "field":
                "urine_protein_dipstick",

            "value":
                protein,

            "message":
                "허용되지 않은 단백뇨 category"
        })

    # -------------------------------------------------
    # 임신여부
    # -------------------------------------------------

    pregnancy_allowed = {
        "pregnant",
        "not_pregnant",
        "unknown"
    }

    pregnancy = get_value(
        data,
        "pregnancy_status"
    )

    if (
        pregnancy is not None
        and pregnancy not in pregnancy_allowed
    ):

        errors.append({
            "field":
                "pregnancy_status",

            "value":
                pregnancy,

            "message":
                "허용되지 않은 임신여부 category"
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
    # 임신인데 주수가 있는 경우 sanity check
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

        valid, message = (
            validate_range(
                field,
                value
            )
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
    # Category 검증
    # -------------------------------------------------

    category_errors = (
        validate_categories(
            data
        )
    )

    validation_errors.extend(
        category_errors
    )

    # -------------------------------------------------
    # Cross-field 검증
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