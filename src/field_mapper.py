import re


FIELD_ALIASES = {

    # 기본 신체계측
    "신장": "height_cm",
    "키": "height_cm",

    "체중": "weight_kg",

    "허리둘레": "HE_wc",
    "허리 둘레": "HE_wc",

    # 혈압
    "수축기혈압": "HE_sbp",
    "수축기 혈압": "HE_sbp",
    "최고혈압": "HE_sbp",

    "이완기혈압": "HE_dbp",
    "이완기 혈압": "HE_dbp",
    "최저혈압": "HE_dbp",

    # 혈당
    "공복혈당": "HE_glu",
    "공복 혈당": "HE_glu",
    "혈당": "HE_glu",

    "당화혈색소": "HE_HbA1c",
    "HbA1c": "HE_HbA1c",

    # 지질
    "총콜레스테롤": "HE_chol",
    "총 콜레스테롤": "HE_chol",
    "Total Cholesterol": "HE_chol",

    "HDL콜레스테롤": "HE_HDL_st2",
    "HDL 콜레스테롤": "HE_HDL_st2",
    "HDL-C": "HE_HDL_st2",

    "중성지방": "HE_TG",
    "Triglyceride": "HE_TG",
    "TG": "HE_TG",

    "LDL콜레스테롤": "HE_LDL_drct",
    "LDL 콜레스테롤": "HE_LDL_drct",
    "LDL-C": "HE_LDL_drct",
    "저밀도지단백콜레스테롤": "HE_LDL_drct",

    # 혈액
    "혈색소": "HE_HB",
    "헤모글로빈": "HE_HB",
    "Hemoglobin": "HE_HB",

    "고감도CRP": "HE_hsCRP",
    "hsCRP": "HE_hsCRP",
    "hs-CRP": "HE_hsCRP",
}


def normalize_name(name):
    """
    OCR 표기 차이를 줄이기 위한 정규화.
    """
    name = name.strip()

    name = re.sub(r"\s+", "", name)

    return name.lower()


NORMALIZED_ALIASES = {
    normalize_name(alias): field
    for alias, field in FIELD_ALIASES.items()
}


def parse_numeric(value):
    """
    '120 mg/dL', '120', '5.4 %' 같은 값을 숫자로 변환.
    """

    if value is None:
        return None

    value = str(value).replace(",", "").strip()

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        value
    )

    if not match:
        return None

    number = float(match.group())

    if number.is_integer():
        return int(number)

    return number


def map_fields(records):
    mapped = {}

    unmapped = []

    for record in records:
        original_name = record["name"]
        normalized = normalize_name(original_name)

        canonical_name = NORMALIZED_ALIASES.get(
            normalized
        )

        if not canonical_name:
            unmapped.append(record)
            continue

        numeric_value = parse_numeric(
            record["value"]
        )

        mapped[canonical_name] = {
            "value": numeric_value,
            "unit": record["unit"],
            "source_name": original_name
        }

    return mapped, unmapped