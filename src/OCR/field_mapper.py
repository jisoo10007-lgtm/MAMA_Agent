import re


# =========================================================
# MAMA HealthExam 26개 Feature Dictionary
#
# 1순위: H01 ~ H26 ID
# 2순위: OCR 항목명 Alias
# =========================================================


# =========================================================
# H ID -> Silver Canonical Field
# =========================================================

FIELD_BY_ID = {
    "H01": "height_cm",
    "H02": "weight_kg",
    "H03": "waist_cm",
    "H04": "bmi_kg_m2",

    # H05, H06은 좌/우 분리 특수 처리
    "H05": "vision_pair",
    "H06": "hearing_pair",

    "H07": "systolic_bp_mmhg",
    "H08": "diastolic_bp_mmhg",

    "H09": "health_exam_hemoglobin_g_dl",
    "H10": "hs_crp_mg_l",

    "H11": "fasting_glucose_mg_dl",
    "H12": "hba1c_pct",

    "H13": "total_cholesterol_mg_dl",
    "H14": "hdl_cholesterol_mg_dl",
    "H15": "triglycerides_mg_dl",
    "H16": "ldl_cholesterol_mg_dl",

    "H17": "ast_u_l",
    "H18": "alt_u_l",
    "H19": "ggt_u_l",

    "H20": "urine_protein_dipstick",

    "H21": "ferritin_ng_ml",
    "H22": "creatinine_mg_dl",
    "H23": "serum_folate_ng_ml",

    # H24 임신여부는 azure_layout.py에서 metadata로 처리
    "H24": "pregnancy_status",

    "H25": "body_temperature_c",
    "H26": "current_hemoglobin_g_dl",
}


# =========================================================
# OCR 이름 -> Silver Canonical Field
# =========================================================

FIELD_ALIASES = {

    # 신체계측
    "신장": "height_cm",
    "키": "height_cm",

    "체중": "weight_kg",

    "허리둘레": "waist_cm",

    "BMI": "bmi_kg_m2",
    "체질량지수": "bmi_kg_m2",

    # 시력
    "시력좌우": "vision_pair",
    "시력(좌/우)": "vision_pair",
    "시력 좌/우": "vision_pair",

    "시력(좌)": "vision_left",
    "좌측시력": "vision_left",
    "시력좌": "vision_left",

    "시력(우)": "vision_right",
    "우측시력": "vision_right",
    "시력우": "vision_right",

    # 청력
    "청력좌우": "hearing_pair",
    "청력(좌/우)": "hearing_pair",
    "청력 좌/우": "hearing_pair",

    "청력(좌)": "hearing_left",
    "좌측청력": "hearing_left",
    "청력좌": "hearing_left",

    "청력(우)": "hearing_right",
    "우측청력": "hearing_right",
    "청력우": "hearing_right",

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

    # 임신
    "임신여부": "pregnancy_status",
    "임신 여부": "pregnancy_status",

    # 현재 상태
    "체온": "body_temperature_c",

    "현재혈색소": "current_hemoglobin_g_dl",
    "현재 혈색소": "current_hemoglobin_g_dl",
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

    if not 1 <= number <= 26:
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
# 좌 / 우 숫자 분리
# =========================================================

def parse_numeric_pair(value):
    """
    예:
    1.0 / 0.8
    1.0, 0.8
    좌 1.0 우 0.8

    -> (1.0, 0.8)
    """

    if value is None:
        return None, None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        str(value)
    )

    if len(numbers) < 2:
        return None, None

    left = float(numbers[0])
    right = float(numbers[1])

    if left.is_integer():
        left = int(left)

    if right.is_integer():
        right = int(right)

    return left, right


# =========================================================
# 혈압 통합값 파싱
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
# =========================================================

def parse_urine_protein(value):

    if value is None:
        return "unknown"

    text = (
        str(value)
        .strip()
        .lower()
    )

    text = re.sub(
        r"\s+",
        "",
        text
    )

    if text in [
        "음성",
        "negative",
        "neg",
        "-",
        "(-)"
    ]:
        return "negative"

    if text in [
        "미량",
        "trace",
        "±",
        "(±)"
    ]:
        return "trace"

    match = re.search(
        r"([1-4])\+",
        text
    )

    if match:
        return f"{match.group(1)}+"

    return "unknown"


# =========================================================
# 청력 한쪽 값 파싱
# =========================================================

def parse_hearing(value):

    if value is None:
        return "unknown"

    text = (
        str(value)
        .strip()
        .lower()
    )

    text = re.sub(
        r"\s+",
        "",
        text
    )

    if text in [
        "정상",
        "normal",
        "정상소견"
    ]:
        return "normal"

    if text in [
        "이상",
        "abnormal",
        "비정상"
    ]:
        return "abnormal"

    return "unknown"


# =========================================================
# 청력 좌 / 우 분리
# =========================================================

def parse_hearing_pair(value):
    """
    예:
    정상 / 정상
    정상, 이상
    좌 정상 우 정상

    -> ("normal", "normal")
    """

    if value is None:
        return None, None

    text = str(value).strip()

    # 먼저 / , | 등의 구분자로 분리
    parts = re.split(
        r"\s*(?:/|,|\||;)\s*",
        text
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if len(parts) >= 2:

        return (
            parse_hearing(parts[0]),
            parse_hearing(parts[1])
        )

    # "좌 정상 우 정상" 형태 fallback
    statuses = re.findall(
        r"정상|비정상|이상|normal|abnormal",
        text,
        flags=re.IGNORECASE
    )

    if len(statuses) >= 2:

        return (
            parse_hearing(statuses[0]),
            parse_hearing(statuses[1])
        )

    return None, None


# =========================================================
# Main Mapping
# =========================================================

def map_fields(records):

    mapped = []
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

        canonical_name = (
            FIELD_BY_ID.get(
                item_id
            )
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
        # H24 임신여부
        #
        # azure_layout.py의 document_info에서
        # 별도로 정규화하므로 여기서는 중복 생성하지 않는다.
        # -------------------------------------------------

        if canonical_name == "pregnancy_status":
            continue

        # -------------------------------------------------
        # H05 시력 좌 / 우
        # -------------------------------------------------

        if canonical_name == "vision_pair":

            left, right = parse_numeric_pair(
                raw_value
            )

            if (
                left is None
                or right is None
            ):

                unmapped.append(
                    record
                )

                continue

            mapped_dict["vision_left"] = {
                "value": left,
                "unit": raw_unit or "decimal acuity",
                "source_name": original_name,
                "source_id": item_id
            }

            mapped_dict["vision_right"] = {
                "value": right,
                "unit": raw_unit or "decimal acuity",
                "source_name": original_name,
                "source_id": item_id
            }

            continue

        # -------------------------------------------------
        # H06 청력 좌 / 우
        # -------------------------------------------------

        if canonical_name == "hearing_pair":

            left, right = parse_hearing_pair(
                raw_value
            )

            if (
                left is None
                or right is None
            ):

                unmapped.append(
                    record
                )

                continue

            mapped_dict["hearing_left"] = {
                "value": left,
                "unit": "category",
                "source_name": original_name,
                "source_id": item_id
            }

            mapped_dict["hearing_right"] = {
                "value": right,
                "unit": "category",
                "source_name": original_name,
                "source_id": item_id
            }

            continue

        # -------------------------------------------------
        # 이전 PDF용 통합 혈압
        # -------------------------------------------------

        if canonical_name == "blood_pressure":

            sbp, dbp = (
                parse_blood_pressure(
                    raw_value
                )
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

            mapped_dict[
                canonical_name
            ] = {
                "value":
                    parse_urine_protein(
                        raw_value
                    ),

                "unit":
                    "category",

                "source_name":
                    original_name,

                "source_id":
                    item_id
            }

            continue

        # -------------------------------------------------
        # 청력 개별 항목 fallback
        # -------------------------------------------------

        if canonical_name in [
            "hearing_left",
            "hearing_right"
        ]:

            mapped_dict[
                canonical_name
            ] = {
                "value":
                    parse_hearing(
                        raw_value
                    ),

                "unit":
                    "category",

                "source_name":
                    original_name,

                "source_id":
                    item_id
            }

            continue

        # -------------------------------------------------
        # 일반 숫자형 검사
        # -------------------------------------------------

        numeric_value = (
            parse_numeric(
                raw_value
            )
        )

        if numeric_value is None:

            unmapped.append(
                record
            )

            continue

        mapped_dict[
            canonical_name
        ] = {
            "value":
                numeric_value,

            "unit":
                raw_unit,

            "source_name":
                original_name,

            "source_id":
                item_id
        }

        # 비고가 실제로 존재하는 경우 보존
        if note and note != "-":

            mapped_dict[
                canonical_name
            ]["note"] = note

    return mapped_dict, unmapped