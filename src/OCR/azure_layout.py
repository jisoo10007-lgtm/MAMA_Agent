import os
import re
import json
import datetime

from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from src.OCR.healthcheck_table_parser import (
    table_to_rows,
    parse_healthcheck_rows,
)

from src.OCR.field_mapper import map_fields

from src.OCR.validator import (
    validate_healthcheck,
    validate_pregnancy_info,
    calculate_bmi,
)

from src.OCR.patient_manager import (
    get_or_create_patient_id,
    normalize_birth_date,
)

from src.Storage.azure_storage import (
    upload_pdf,
    upload_json,
)

# ==================================================
# 환경변수
# ==================================================

load_dotenv()

endpoint = os.getenv(
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
)

key = os.getenv(
    "AZURE_DOCUMENT_INTELLIGENCE_KEY"
)

if not endpoint:
    raise ValueError(
        "Azure Document Intelligence endpoint가 없습니다."
    )

if not key:
    raise ValueError(
        "Azure Document Intelligence key가 없습니다."
    )


# ==================================================
# Azure Client
# ==================================================

client = DocumentIntelligenceClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)


# ==================================================
# Azure Layout
# ==================================================

def analyze_layout(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {file_path}"
        )

    with open(file_path, "rb") as f:

        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=f
        )

    return poller.result()


# ==================================================
# OCR 전체 Text
# ==================================================

def get_full_text(result):

    lines = []

    for page in result.pages:

        if not page.lines:
            continue

        for line in page.lines:

            text = line.content.strip()

            if text:
                lines.append(text)

    return "\n".join(lines)


# ==================================================
# 날짜 정규화
# ==================================================

def normalize_ocr_date(value):

    if not value:
        return None

    numbers = re.findall(
        r"\d+",
        str(value)
    )

    if len(numbers) != 3:
        return None

    year, month, day = numbers

    if len(year) != 4:
        return None

    try:

        date_value = datetime.date(
            int(year),
            int(month),
            int(day)
        )

        return date_value.strftime(
            "%Y-%m-%d"
        )

    except ValueError:
        return None


# ==================================================
# 임신여부 정규화
# ==================================================

def parse_pregnancy_status(value, info):
    """
    예:

    비임신
        -> not_pregnant
        -> gestational_weeks = None

    임신(26주차)
        -> pregnant
        -> gestational_weeks = 26
    """

    if not value:
        return

    text = str(value).strip()

    # 비임신에도 "임신" 문자열이 포함되므로 먼저 검사
    if "비임신" in text:

        info["pregnancy_status_raw"] = text
        info["pregnancy_status"] = "not_pregnant"
        info["gestational_weeks"] = None

        return

    if "임신" in text:

        info["pregnancy_status_raw"] = text
        info["pregnancy_status"] = "pregnant"

        week_match = re.search(
            r"(\d+)\s*주",
            text
        )

        if week_match:

            info["gestational_weeks"] = int(
                week_match.group(1)
            )

        return

    info["pregnancy_status_raw"] = text
    info["pregnancy_status"] = "unknown"
    info["gestational_weeks"] = None


# ==================================================
# 문서 / 환자정보 추출
# ==================================================

def extract_document_info(result):

    info = {
        "name": None,
        "birth_date": None,
        "exam_date": None,
        "institution_name": None,
        "pregnancy_status_raw": None,
        "pregnancy_status": None,
        "gestational_weeks": None
    }

    # --------------------------------------------------
    # Table 우선
    # --------------------------------------------------

    for table in result.tables or []:

        rows = table_to_rows(table)

        for row in rows:

            for i in range(
                0,
                len(row) - 1,
                2
            ):

                key_name = row[i].strip()
                value = row[i + 1].strip()

                if not key_name:
                    continue

                if key_name in [
                    "성 명",
                    "성명",
                    "수검자",
                    "이름"
                ]:

                    info["name"] = value

                elif key_name == "생년월일":

                    info["birth_date"] = (
                        normalize_ocr_date(value)
                    )

                elif key_name in [
                    "검진일",
                    "검사일"
                ]:

                    info["exam_date"] = (
                        normalize_ocr_date(value)
                    )

                elif key_name in [
                    "검진기관명",
                    "검진기관",
                    "의료기관명",
                    "의료기관"
                ]:

                    info["institution_name"] = value

                elif key_name in [
                    "임신여부",
                    "임신 여부"
                ]:

                    parse_pregnancy_status(
                        value,
                        info
                    )

    # --------------------------------------------------
    # OCR Text fallback
    # --------------------------------------------------

    full_text = get_full_text(result)

    # 이름
    if not info["name"]:

        match = re.search(
            r"(?:성\s*명|성명|수검자|이름)"
            r"\s*[:：]?\s*"
            r"([가-힣]{2,5})",
            full_text
        )

        if match:
            info["name"] = match.group(1)

    # 생년월일
    if not info["birth_date"]:

        match = re.search(
            r"생년월일\s*[:：]?\s*"
            r"(\d{4}\s*[-./]\s*"
            r"\d{1,2}\s*[-./]\s*"
            r"\d{1,2})",
            full_text
        )

        if match:

            info["birth_date"] = (
                normalize_ocr_date(
                    match.group(1)
                )
            )

    # 검진일
    if not info["exam_date"]:

        match = re.search(
            r"(?:검진일|검사일)"
            r"\s*[:：]?\s*"
            r"(\d{4}\s*[-./]\s*"
            r"\d{1,2}\s*[-./]\s*"
            r"\d{1,2})",
            full_text
        )

        if match:

            info["exam_date"] = (
                normalize_ocr_date(
                    match.group(1)
                )
            )

    # 검진기관명
    if not info["institution_name"]:

        match = re.search(
            r"(?:검진기관명|검진기관|의료기관명|의료기관)"
            r"\s*[:：]?\s*([^\n]+)",
            full_text
        )

        if match:

            info["institution_name"] = (
                match.group(1).strip()
            )

    # 임신여부
    if not info["pregnancy_status"]:

        match = re.search(
            r"임신\s*여부"
            r"\s*[:：]?\s*([^\n]+)",
            full_text
        )

        if match:

            parse_pregnancy_status(
                match.group(1),
                info
            )

    return info


# ==================================================
# 검사결과 Table 판단
# ==================================================

def is_healthcheck_table(table):

    table_text = " ".join(
        (cell.content or "")
        for cell in table.cells
    )

    required_keywords = [
        "검사항목",
        "결과",
        "단위"
    ]

    matched = sum(
        keyword in table_text
        for keyword in required_keywords
    )

    return matched >= 2


# ==================================================
# 건강검진 데이터 추출
# ==================================================

def extract_healthcheck(result):

    records = []

    for table in result.tables or []:

        if not is_healthcheck_table(table):
            continue

        rows = table_to_rows(table)

        parsed = parse_healthcheck_rows(
            rows
        )

        records.extend(parsed)

    return records


# ==================================================
# 날짜 -> 파일명
# ==================================================

def date_to_filename(date_string):

    if not date_string:
        return "unknown_date"

    return re.sub(
        r"\D",
        "",
        date_string
    )


# ==================================================
# JSON 저장
# ==================================================

def save_json(data, file_path):

    directory = os.path.dirname(
        file_path
    )

    os.makedirs(
        directory,
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==================================================
# 하나의 건강검진 PDF 처리
# ==================================================

def process_healthcheck(input_file):

    print("\n" + "=" * 55)
    print("MAMA Agent Healthcheck Pipeline")
    print("=" * 55)

    # --------------------------------------------------
    # 1. Azure 분석
    # --------------------------------------------------

    print("\n[1] Azure 분석")
    print("파일:", input_file)

    result = analyze_layout(
        input_file
    )

    print(
        "페이지:",
        len(result.pages)
    )

    print(
        "테이블:",
        len(result.tables or [])
    )

    # --------------------------------------------------
    # 2. 문서 / 환자정보
    # --------------------------------------------------

    print("\n[2] 문서 / 환자정보")

    document_info = extract_document_info(
        result
    )

    print(
        "이름:",
        document_info["name"]
    )

    print(
        "생년월일:",
        document_info["birth_date"]
    )

    print(
        "검진일:",
        document_info["exam_date"]
    )

    print(
        "검진기관명:",
        document_info["institution_name"]
    )

    print(
        "임신여부:",
        document_info["pregnancy_status"]
    )

    print(
        "임신여부 원문:",
        document_info["pregnancy_status_raw"]
    )

    print(
        "임신주수:",
        document_info["gestational_weeks"]
    )

    # --------------------------------------------------
    # 필수 환자정보 확인
    # --------------------------------------------------

    if not document_info["name"]:
        raise ValueError(
            "환자 이름 추출 실패"
        )

    if not document_info["birth_date"]:
        raise ValueError(
            "생년월일 추출 실패"
        )

    if not document_info["exam_date"]:
        raise ValueError(
            "검진일 추출 실패"
        )

    birth_date = normalize_birth_date(
        document_info["birth_date"]
    )

    # --------------------------------------------------
    # 3. Patient ID
    # --------------------------------------------------

    print("\n[3] Patient ID")

    patient_id = get_or_create_patient_id(
        document_info["name"],
        birth_date
    )

    print(patient_id)

    # --------------------------------------------------
    # 4. 검사결과 파싱
    # --------------------------------------------------

    print("\n[4] 검사결과 파싱")

    records = extract_healthcheck(
        result
    )

    mapped, unmapped = map_fields(
        records
    )

    print(
        "사용 검사:",
        len(mapped)
    )

    # --------------------------------------------------
    # BMI 계산
    # --------------------------------------------------

    height = (
        mapped
        .get("height_cm", {})
        .get("value")
    )

    weight = (
        mapped
        .get("weight_kg", {})
        .get("value")
    )

    calculated_bmi = calculate_bmi(
        height,
        weight
    )

    if calculated_bmi is not None:

        # PDF에 BMI 값이 없는 경우
        if "bmi_kg_m2" not in mapped:

            mapped["bmi_kg_m2"] = {
                "value": calculated_bmi,
                "unit": "kg/m²",
                "source_name": "calculated"
            }

        # PDF에 BMI 값이 이미 있는 경우
        else:

            mapped[
                "bmi_kg_m2"
            ][
                "calculated_value"
            ] = calculated_bmi

    print(
        "계산 BMI:",
        calculated_bmi
    )

    # --------------------------------------------------
    # 임신여부를 Healthcheck에도 연결
    # --------------------------------------------------

    if document_info["pregnancy_status"]:

        mapped["pregnancy_status"] = {

            "value":
                document_info[
                    "pregnancy_status"
                ],

            "raw_value":
                document_info[
                    "pregnancy_status_raw"
                ],

            "unit":
                "category",

            "source_name":
                "임신여부"
        }

    # --------------------------------------------------
    # 5. Healthcheck Validation
    # --------------------------------------------------

    validation_errors = (
        validate_healthcheck(
            mapped
        )
    )

    # --------------------------------------------------
    # 6. Pregnancy Validation
    # --------------------------------------------------

    pregnancy_validation_errors = (
        validate_pregnancy_info({

            "status":
                document_info[
                    "pregnancy_status"
                ],

            "gestational_weeks":
                document_info[
                    "gestational_weeks"
                ]
        })
    )

    # 건강검진 검증 결과 + 임신정보 검증 결과
    validation_errors.extend(
        pregnancy_validation_errors
    )

    print(
        "Validation 오류:",
        len(validation_errors)
    )

    # --------------------------------------------------
    # 7. 최종 JSON
    # --------------------------------------------------

    output = {

        "patient_id":
            patient_id,

        "patient_info": {

            "name":
                document_info["name"],

            "birth_date":
                birth_date
        },

        "exam_info": {

            "exam_date":
                document_info[
                    "exam_date"
                ],

            "institution_name":
                document_info[
                    "institution_name"
                ]
        },

        "pregnancy_info": {

            "raw":
                document_info[
                    "pregnancy_status_raw"
                ],

            "status":
                document_info[
                    "pregnancy_status"
                ],

            "gestational_weeks":
                document_info[
                    "gestational_weeks"
                ]
        },

        "healthcheck":
            mapped,

        "validation_errors":
            validation_errors,

        "unmapped_fields":
            unmapped
    }

        # --------------------------------------------------
    # 8. 저장
    # --------------------------------------------------

    exam_date = document_info["exam_date"]

    exam_file = date_to_filename(
        exam_date
    )

    # 로컬 JSON 저장
    output_file = os.path.join(
        "output",
        patient_id,
        f"{exam_file}.json"
    )

    save_json(
        output,
        output_file
    )

    print("\n[5] 로컬 저장 완료")
    print(output_file)

    # --------------------------------------------------
    # 9. Azure Storage 저장
    # --------------------------------------------------

    pdf_blob = upload_pdf(
        file_path=input_file,
        patient_id=patient_id,
        exam_date=exam_date,
    )

    json_blob = upload_json(
        data=output,
        patient_id=patient_id,
        exam_date=exam_date,
    )

    print("\n[6] Azure Storage 저장 완료")
    print("PDF :", pdf_blob)
    print("JSON:", json_blob)

    output["storage"] = {
        "raw": pdf_blob,
        "processed": json_blob,
    }

    return output

# ==================================================
# 실행
# ==================================================

if __name__ == "__main__":

    input_file = (
        "data/patient_02_healthcheck.pdf"
    )

    process_healthcheck(
        input_file
    )