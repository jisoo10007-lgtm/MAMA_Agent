import re


# =========================================================
# MAMA HealthExam - X_exam 기준 23개 Feature Dictionary
# =========================================================


# =========================================================
# H ID -> Canonical Field
# =========================================================

FIELD_BY_ID = {
    "H01": "height_cm",
    "H02": "weight_kg",
    "H03": "waist_cm",
    "H04": "bmi_kg_m2",

    "H05": "systolic_bp_mmhg",
    "H06": "diastolic_bp_mmhg",

    "H07": "health_exam_hemoglobin_g_dl",
    "H08": "hs_crp_mg_l",

    "H09": "fasting_glucose_mg_dl",
    "H10": "hba1c_pct",

    "H11": "total_cholesterol_mg_dl",
    "H12": "hdl_cholesterol_mg_dl",
    "H13": "triglycerides_mg_dl",
    "H14": "ldl_cholesterol_mg_dl",

    "H15": "ast_u_l",
    "H16": "alt_u_l",
    "H17": "ggt_u_l",

    "H18": "urine_protein_dipstick",

    "H19": "ferritin_ng_ml",
    "H20": "creatinine_mg_dl",
    "H21": "serum_folate_ng_ml",

    "H22": "gestational_age_days",
    "H23": "body_temperature_c",
}


# =========================================================
# OCR 이름 -> Canonical Field
# =========================================================

FIELD_ALIASES = {

    # 신체계측
    "신장": "height_cm",
    "키": "height_cm",

    "체중": "weight_kg",

    "허리둘레": "waist_cm",

    "BMI": "bmi_kg_m2",
    "체질량지수": "bmi_kg_m2",

    # 혈압
    "수축기혈압": "systolic_bp_mmhg",
    "수축기 혈압": "systolic_bp_mmhg",
    "수축기 혈압(SBP)": "systolic_bp_mmhg",
    "최고혈압": "systolic_bp_mmhg",
    "SBP": "systolic_bp_mmhg",

    "이완기혈압": "diastolic_bp_mmhg",
    "이완기 혈압": "diastolic_bp_mmhg",
    "이완기 혈압(DBP)": "diastolic_bp_mmhg",
    "최저혈압": "diastolic_bp_mmhg",
    "DBP": "diastolic_bp_mmhg",

    # 이전 PDF 호환용
    "혈압(최고/최저)": "blood_pressure",
    "혈압": "blood_pressure",

    # 혈액 / 염증
    "검진혈색소": "health_exam_hemoglobin_g_dl",
    "검진 혈색소": "health_exam_hemoglobin_g_dl",
    "혈색소": "health_exam_hemoglobin_g_dl",
    "헤모글로빈": "health_exam_hemoglobin_g_dl",
    "Hemoglobin": "health_exam_hemoglobin_g_dl",

    "고감도C반응단백": "hs_crp_mg_l",
    "고감도 C반응단백": "hs_crp_mg_l",
    "hs-CRP": "hs_crp_mg_l",
    "hsCRP": "hs_crp_mg_l",

    # 당대사
    "공복혈당": "fasting_glucose_mg_dl",
    "FBS": "fasting_glucose_mg_dl",

    "당화혈색소": "hba1c_pct",
    "HbA1c": "hba1c_pct",

    # 지질
    "총콜레스테롤": "total_cholesterol_mg_dl",
    "Total Cholesterol": "total_cholesterol_mg_dl",

    "HDL-콜레스테롤": "hdl_cholesterol_mg_dl",
    "HDL콜레스테롤": "hdl_cholesterol_mg_dl",
    "HDL": "hdl_cholesterol_mg_dl",

    "중성지방": "triglycerides_mg_dl",
    "TG": "triglycerides_mg_dl",

    "LDL-콜레스테롤": "ldl_cholesterol_mg_dl",
    "LDL콜레스테롤": "ldl_cholesterol_mg_dl",
    "LDL": "ldl_cholesterol_mg_dl",

    # 간기능
    "AST": "ast_u_l",
    "AST(SGOT)": "ast_u_l",
    "SGOT": "ast_u_l",

    "ALT": "alt_u_l",
    "ALT(SGPT)": "alt_u_l",
    "SGPT": "alt_u_l",

    "γ-GTP": "ggt_u_l",
    "γGTP": "ggt_u_l",
    "감마GTP": "ggt_u_l",
    "GGT": "ggt_u_l",

    # 소변
    "단백뇨": "urine_protein_dipstick",
    "요단백": "urine_protein_dipstick",

    # 추가 혈액검사
    "페리틴": "ferritin_ng_ml",
    "Ferritin": "ferritin_ng_ml",

    "혈중크레아티닌": "creatinine_mg_dl",
    "혈중 크레아티닌": "creatinine_mg_dl",
    "혈청크레아티닌": "creatinine_mg_dl",
    "크레아티닌": "creatinine_mg_dl",
    "Creatinine": "creatinine_mg_dl",

    "혈청엽산": "serum_folate_ng_ml",
    "혈청 엽산": "serum_folate_ng_ml",
    "엽산": "serum_folate_ng_ml",

    # 임신주수
    "임신주수": "gestational_age_days",
    "임신 주수": "gestational_age_days",
    "재태주수": "gestational_age_days",
    "재태 주수": "gestational_age_days",

    # 체온
    "체온": "body_temperature_c",
    "체온측정": "body_temperature_c",
}


# =========================================================
# 이름 정규화
# =========================================================

def normalize_name(name):

    if not name:
        return ""

    name = str(name).strip()

    # 모든 공백 제거
    name = re.sub(
        r"\s+",
        "",
        name
    )

    # 하이픈 계열 제거
    name = re.sub(
        r"[-‐‒–—−]",
        "",
        name
    )

    return name.lower()


NORMALIZED_ALIASES = {
    normalize_name(alias): field
    for alias, field in FIELD_ALIASES.items()
}


# =========================================================
# H ID 정규화
# =========================================================

def normalize_item_id(item_id):

    if not item_id:
        return ""

    text = str(item_id).strip().upper()

    # OCR 공백 제거
    text = re.sub(
        r"\s+",
        "",
        text
    )

    match = re.fullmatch(
        r"H(\d{1,2})",
        text
    )

    if not match:
        return ""

    number = int(
        match.group(1)
    )

    if not 1 <= number <= 23:
        return ""

    return f"H{number:02d}"


# =========================================================
# 숫자 파싱
# =========================================================

def parse_numeric(value):

    if value is None:
        return None

    value = (
        str(value)
        .replace(",", "")
        .strip()
    )

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


# =========================================================
# 혈압 통합값 파싱
# 이전 PDF 호환용
# =========================================================

def parse_blood_pressure(value):

    if not value:
        return None, None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        str(value)
    )

    if len(numbers) < 2:
        return None, None

    systolic = float(numbers[0])
    diastolic = float(numbers[1])

    if systolic.is_integer():
        systolic = int(systolic)

    if diastolic.is_integer():
        diastolic = int(diastolic)

    return systolic, diastolic


# =========================================================
# 단백뇨 파싱
#
# X_exam:
# urine_protein_dipstick = DOUBLE
#
# 숫자값은 그대로 유지한다.
# 음성/negative는 0으로 변환한다.
# =========================================================

def parse_urine_protein(value):

    if value is None:
        return None

    text = str(value).strip().lower()

    # 숫자로 들어온 경우
    # 예: 0 / 1 / 2
    if re.fullmatch(
        r"-?\d+(?:\.\d+)?",
        text
    ):

        number = float(text)

        if number.is_integer():
            return int(number)

        return number

    text = re.sub(
        r"\s+",
        "",
        text
    )

    # 기존 표현 호환
    if text in [
        "음성",
        "negative",
        "neg",
        "-",
        "(-)"
    ]:
        return 0

    # 현재 X_exam의 정확한 trace / + 변환 규칙은
    # 확인되지 않았으므로 임의 변환하지 않는다.
    return None


# =========================================================
# 임신주수 -> gestational_age_days
#
# 예:
# 31주 4일 -> 221
# 31주     -> 217
# 221      -> 221
# =========================================================

def parse_gestational_age_days(value):

    if value is None:
        return None

    text = str(value).strip()

    # "31주 4일"
    # "31 주 4 일"
    # "31주"
    match = re.search(
        r"(\d+)\s*주(?:\s*(\d+)\s*일)?",
        text
    )

    if match:

        weeks = int(
            match.group(1)
        )

        days = int(
            match.group(2) or 0
        )

        return (
            weeks * 7
            + days
        )

    # 이미 일수 형태의 숫자로 들어온 경우
    numeric = parse_numeric(
        text
    )

    if numeric is not None:
        return numeric

    return None


# =========================================================
# Main Mapping
# =========================================================

def map_fields(records):

    mapped_dict = {}
    unmapped = []

    for record in records:

        item_id = normalize_item_id(
            record.get(
                "item_id",
                ""
            )
        )

        original_name = record.get(
            "name",
            ""
        )

        raw_value = record.get(
            "value"
        )

        raw_unit = record.get(
            "unit",
            ""
        )

        note = record.get(
            "note",
            ""
        )

        # -------------------------------------------------
        # 1순위: H ID
        # -------------------------------------------------

        canonical_name = FIELD_BY_ID.get(
            item_id
        )

        # -------------------------------------------------
        # 2순위: 이름 fallback
        # -------------------------------------------------

        if not canonical_name:

            normalized = normalize_name(
                original_name
            )

            canonical_name = (
                NORMALIZED_ALIASES.get(
                    normalized
                )
            )

        # -------------------------------------------------
        # 매핑 실패
        # -------------------------------------------------

        if not canonical_name:

            unmapped.append(
                record
            )

            continue

        # -------------------------------------------------
        # 이전 PDF용 통합 혈압
        # -------------------------------------------------

        if canonical_name == "blood_pressure":

            sbp, dbp = parse_blood_pressure(
                raw_value
            )

            if (
                sbp is None
                or dbp is None
            ):

                unmapped.append(
                    record
                )

                continue

            mapped_dict[
                "systolic_bp_mmhg"
            ] = {
                "value": sbp,
                "unit": "mmHg",
                "source_name": original_name,
                "source_id": item_id
            }

            mapped_dict[
                "diastolic_bp_mmhg"
            ] = {
                "value": dbp,
                "unit": "mmHg",
                "source_name": original_name,
                "source_id": item_id
            }

            continue

        # -------------------------------------------------
        # 단백뇨
        # -------------------------------------------------

        if (
            canonical_name
            == "urine_protein_dipstick"
        ):

            urine_value = parse_urine_protein(
                raw_value
            )

            if urine_value is None:

                unmapped.append(
                    record
                )

                continue

            mapped_dict[
                canonical_name
            ] = {
                "value": urine_value,
                "unit": raw_unit or "grade",
                "source_name": original_name,
                "source_id": item_id
            }

            if note and note != "-":

                mapped_dict[
                    canonical_name
                ]["note"] = note

            continue

        # -------------------------------------------------
        # 임신주수 -> gestational age days
        # -------------------------------------------------

        if (
            canonical_name
            == "gestational_age_days"
        ):

            gestational_days = (
                parse_gestational_age_days(
                    raw_value
                )
            )

            if gestational_days is None:

                unmapped.append(
                    record
                )

                continue

            mapped_dict[
                canonical_name
            ] = {
                "value": gestational_days,
                "unit": "days",
                "source_name": original_name,
                "source_id": item_id
            }

            if note and note != "-":

                mapped_dict[
                    canonical_name
                ]["note"] = note

            continue

        # -------------------------------------------------
        # 일반 숫자형 검사
        # -------------------------------------------------

        numeric_value = parse_numeric(
            raw_value
        )

        if numeric_value is None:

            unmapped.append(
                record
            )

            continue

        mapped_dict[
            canonical_name
        ] = {
            "value": numeric_value,
            "unit": raw_unit,
            "source_name": original_name,
            "source_id": item_id
        }

        # 비고가 실제로 존재하는 경우 보존
        if note and note != "-":

            mapped_dict[
                canonical_name
            ]["note"] = note

    return mapped_dict, unmapped