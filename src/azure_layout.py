import os
import re
import json
import datetime

from dotenv import load_dotenv

from azure.core.credentials import (
    AzureKeyCredential
)

from azure.ai.documentintelligence import (
    DocumentIntelligenceClient
)

from healthcheck_table_parser import (
    table_to_rows,
    parse_healthcheck_rows
)

from field_mapper import (
    map_fields
)

from validator import (
    validate_healthcheck,
    calculate_bmi
)

from patient_manager import (
    get_or_create_patient_id,
    normalize_birth_date
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
    credential=AzureKeyCredential(
        key
    )
)


# ==================================================
# Azure Layout
# ==================================================

def analyze_layout(file_path):

    if not os.path.exists(
        file_path
    ):

        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: {file_path}"
        )

    with open(
        file_path,
        "rb"
    ) as f:

        poller = (
            client.begin_analyze_document(
                model_id="prebuilt-layout",
                body=f
            )
        )

    return poller.result()


# ==================================================
# OCR Text
# ==================================================

def get_full_text(result):

    lines = []

    for page in result.pages:

        if not page.lines:
            continue

        for line in page.lines:

            text = (
                line.content.strip()
            )

            if text:
                lines.append(text)

    return "\n".join(
        lines
    )


# ==================================================
# 날짜 정규화
# ==================================================

def normalize_ocr_date(value):

    if not value:
        return None

    numbers = re.findall(
        r"\d+",
        value
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
# 환자정보 추출
# ==================================================

def extract_patient_info(result):

    patient_info = {
        "name": None,
        "birth_date": None,
        "exam_date": None
    }

    # ----------------------------------------------
    # Table 우선
    # ----------------------------------------------

    for table in result.tables or []:

        rows = table_to_rows(
            table
        )

        for row in rows:

            for i in range(
                0,
                len(row) - 1,
                2
            ):

                key_name = (
                    row[i].strip()
                )

                value = (
                    row[i + 1]
                    .strip()
                )

                if key_name in [
                    "성 명",
                    "성명",
                    "수검자",
                    "이름"
                ]:

                    patient_info[
                        "name"
                    ] = value

                elif key_name == "생년월일":

                    patient_info[
                        "birth_date"
                    ] = (
                        normalize_ocr_date(
                            value
                        )
                    )

                elif key_name in [
                    "검진일",
                    "검사일"
                ]:

                    patient_info[
                        "exam_date"
                    ] = (
                        normalize_ocr_date(
                            value
                        )
                    )

    # ----------------------------------------------
    # OCR Text fallback
    # ----------------------------------------------

    full_text = get_full_text(
        result
    )

    if not patient_info["name"]:

        match = re.search(
            r"(?:성\s*명|성명|수검자|이름)\s*"
            r"([가-힣]{2,5})",
            full_text
        )

        if match:

            patient_info[
                "name"
            ] = match.group(1)

    if not patient_info["birth_date"]:

        match = re.search(
            r"생년월일\s*"
            r"(\d{4}\s*[-./]\s*"
            r"\d{1,2}\s*[-./]\s*"
            r"\d{1,2})",
            full_text
        )

        if match:

            patient_info[
                "birth_date"
            ] = normalize_ocr_date(
                match.group(1)
            )

    if not patient_info["exam_date"]:

        match = re.search(
            r"(?:검진일|검사일)\s*"
            r"(\d{4}\s*[-./]\s*"
            r"\d{1,2}\s*[-./]\s*"
            r"\d{1,2})",
            full_text
        )

        if match:

            patient_info[
                "exam_date"
            ] = normalize_ocr_date(
                match.group(1)
            )

    return patient_info


# ==================================================
# 검사결과 Table 판단
# ==================================================

def is_healthcheck_table(
    table
):

    table_text = " ".join(
        cell.content
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

def extract_healthcheck(
    result
):

    records = []

    for table in result.tables or []:

        if not is_healthcheck_table(
            table
        ):
            continue

        rows = table_to_rows(
            table
        )

        parsed = (
            parse_healthcheck_rows(
                rows
            )
        )

        records.extend(
            parsed
        )

    return records


# ==================================================
# 날짜 -> 파일명
# ==================================================

def date_to_filename(
    date_string
):

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

def save_json(
    data,
    file_path
):

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

def process_healthcheck(
    input_file
):

    print(
        "\n" + "=" * 55
    )

    print(
        "MAMA Agent Healthcheck Pipeline"
    )

    print(
        "=" * 55
    )

    # ----------------------------------------------
    # Azure
    # ----------------------------------------------

    print(
        "\n[1] Azure 분석"
    )

    print(
        "파일:",
        input_file
    )

    result = analyze_layout(
        input_file
    )

    print(
        "페이지:",
        len(result.pages)
    )

    print(
        "테이블:",
        len(result.tables)
    )

    # ----------------------------------------------
    # 환자정보
    # ----------------------------------------------

    print(
        "\n[2] 환자정보"
    )

    patient_info = (
        extract_patient_info(
            result
        )
    )

    print(
        "이름:",
        patient_info["name"]
    )

    print(
        "생년월일:",
        patient_info["birth_date"]
    )

    print(
        "검진일:",
        patient_info["exam_date"]
    )

    if not patient_info["name"]:

        raise ValueError(
            "환자 이름 추출 실패"
        )

    if not patient_info["birth_date"]:

        raise ValueError(
            "생년월일 추출 실패"
        )

    if not patient_info["exam_date"]:

        raise ValueError(
            "검진일 추출 실패"
        )

    birth_date = normalize_birth_date(
        patient_info["birth_date"]
    )

    # ----------------------------------------------
    # Patient ID
    # ----------------------------------------------

    print(
        "\n[3] Patient ID"
    )

    patient_id = (
        get_or_create_patient_id(
            patient_info["name"],
            birth_date
        )
    )

    print(
        patient_id
    )

    # ----------------------------------------------
    # 검사결과
    # ----------------------------------------------

    print(
        "\n[4] 검사결과 파싱"
    )

    records = extract_healthcheck(
        result
    )

    mapped, unmapped = (
        map_fields(
            records
        )
    )

    print(
        "사용 검사:",
        len(mapped)
    )

    # ----------------------------------------------
    # BMI
    # ----------------------------------------------

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

    bmi = calculate_bmi(
        height,
        weight
    )

    if bmi is not None:

        mapped["HE_BMI"] = {
            "value": bmi,
            "unit": "kg/m²",
            "source_name": "calculated"
        }

    print(
        "BMI:",
        bmi
    )

    # ----------------------------------------------
    # Validation
    # ----------------------------------------------

    validation_errors = (
        validate_healthcheck(
            mapped
        )
    )

    print(
        "Validation 오류:",
        len(validation_errors)
    )

    # ----------------------------------------------
    # JSON
    # ----------------------------------------------

    output = {

        "patient_id":
            patient_id,

        "patient_info": {

            "name":
                patient_info["name"],

            "birth_date":
                birth_date
        },

        "exam_info": {

            "exam_date":
                patient_info[
                    "exam_date"
                ]
        },

        "healthcheck":
            mapped,

        "validation_errors":
            validation_errors,

        "unmapped_fields":
            unmapped
    }

    # ----------------------------------------------
    # 저장
    # ----------------------------------------------

    exam_file = (
        date_to_filename(
            patient_info[
                "exam_date"
            ]
        )
    )

    output_file = os.path.join(
        "output",
        patient_id,
        f"{exam_file}.json"
    )

    save_json(
        output,
        output_file
    )

    print(
        "\n[5] 저장 완료"
    )

    print(
        output_file
    )

    return output


# ==================================================
# 실행
# ==================================================

if __name__ == "__main__":

    input_file = (
        "data/patient_04_healthcheck.pdf"
    )

    process_healthcheck(
        input_file
    )