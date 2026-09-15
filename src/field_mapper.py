import re


FIELD_ALIASES = {

    # 신체계측
    "신장": "height_cm",
    "체중": "weight_kg",
    "허리둘레": "HE_wc",

    # 혈압
    "혈압(최고/최저)": "blood_pressure",

    # 혈당
    "공복혈당": "HE_glu",
    "당화혈색소": "HE_HbA1c",

    # 지질
    "총콜레스테롤": "HE_chol",
    "HDL-콜레스테롤": "HE_HDL_st2",
    "중성지방": "HE_TG",
    "LDL-콜레스테롤": "HE_LDL_drct",

    # 혈액
    "혈색소": "HE_HB",

    # 염증
    "고감도 C반응단백": "HE_hsCRP"
}


def normalize_name(name):
    """
    Azure OCR의 공백/하이픈 차이를 제거한다.

    HDL - 콜레스테롤
    HDL-콜레스테롤

    -> hdl콜레스테롤
    """

    if not name:
        return ""

    name = str(name).strip()

    # 공백 제거
    name = re.sub(
        r"\s+",
        "",
        name
    )

    # 하이픈 제거
    name = re.sub(
        r"[-‐-‒–—−]",
        "",
        name
    )

    return name.lower()


NORMALIZED_ALIASES = {

    normalize_name(alias): field

    for alias, field
    in FIELD_ALIASES.items()
}


def parse_numeric(value):
    """
    일반 숫자 추출
    """

    if value is None:
        return None

    value = str(value).replace(
        ",",
        ""
    ).strip()

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        value
    )

    if not match:
        return None

    number = float(
        match.group()
    )

    if number.is_integer():
        return int(number)

    return number


def parse_blood_pressure(value):
    """
    118 / 76
    118/76
    118 - 76

    -> (118, 76)
    """

    if not value:
        return None, None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        str(value)
    )

    if len(numbers) < 2:
        return None, None

    sbp = float(numbers[0])
    dbp = float(numbers[1])

    if sbp.is_integer():
        sbp = int(sbp)

    if dbp.is_integer():
        dbp = int(dbp)

    return sbp, dbp


def map_fields(records):

    mapped = {}
    unmapped = []

    for record in records:

        original_name = record.get(
            "name",
            ""
        )

        normalized = normalize_name(
            original_name
        )

        canonical_name = (
            NORMALIZED_ALIASES.get(
                normalized
            )
        )

        # MAMA에서 사용하지 않는 검사
        if not canonical_name:

            continue

        # ------------------------------------------
        # 혈압
        # ------------------------------------------

        if canonical_name == "blood_pressure":

            sbp, dbp = parse_blood_pressure(
                record.get("value")
            )

            if sbp is None or dbp is None:

                unmapped.append(
                    record
                )

                continue

            mapped["HE_sbp"] = {
                "value": sbp,
                "unit": "mmHg",
                "source_name": original_name
            }

            mapped["HE_dbp"] = {
                "value": dbp,
                "unit": "mmHg",
                "source_name": original_name
            }

            continue

        # ------------------------------------------
        # 일반 검사
        # ------------------------------------------

        numeric_value = parse_numeric(
            record.get("value")
        )

        if numeric_value is None:

            unmapped.append(
                record
            )

            continue

        mapped[
            canonical_name
        ] = {
            "value": numeric_value,
            "unit": record.get(
                "unit",
                ""
            ),
            "source_name": original_name
        }

    return mapped, unmapped