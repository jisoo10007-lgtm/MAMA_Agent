def validate_range(field, value):

    if value is None:
        return False, "값 없음"

    # OCR/파싱 오류 탐지를 위한 sanity range
    # 임상 진단 기준이 아님
    ranges = {

        "height_cm": (100, 220),
        "weight_kg": (30, 250),

        "HE_wc": (40, 200),

        "HE_sbp": (60, 250),
        "HE_dbp": (30, 150),

        "HE_glu": (30, 500),
        "HE_HbA1c": (2, 20),

        "HE_chol": (50, 500),
        "HE_HDL_st2": (10, 150),
        "HE_TG": (20, 1500),
        "HE_LDL_drct": (10, 400),

        "HE_HB": (5, 25),

        "HE_hsCRP": (0, 100),

        "HE_BMI": (10, 80)
    }

    if field not in ranges:
        return True, None

    min_value, max_value = ranges[
        field
    ]

    if min_value <= value <= max_value:
        return True, None

    return (
        False,
        f"허용 범위 벗어남: {value}"
    )


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


def validate_cross_fields(data):

    errors = []

    sbp = get_value(
        data,
        "HE_sbp"
    )

    dbp = get_value(
        data,
        "HE_dbp"
    )

    if (
        sbp is not None
        and dbp is not None
    ):

        if sbp <= dbp:

            errors.append(
                "수축기혈압은 이완기혈압보다 커야 합니다."
            )

    return errors


def validate_healthcheck(data):

    validation_errors = []

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
                "field": field,
                "value": value,
                "message": message
            })

    cross_errors = (
        validate_cross_fields(
            data
        )
    )

    for error in cross_errors:

        validation_errors.append({
            "field": "cross_field",
            "message": error
        })

    return validation_errors