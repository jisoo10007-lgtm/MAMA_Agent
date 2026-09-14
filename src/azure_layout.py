import os
import json

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import (
    DocumentIntelligenceClient
)

from healthcheck_table_parser import (
    table_to_rows,
    parse_healthcheck_rows
)

from field_mapper import map_fields


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


client = DocumentIntelligenceClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)


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


def extract_healthcheck(result):

    all_records = []

    for table in result.tables:

        rows = table_to_rows(table)

        records = parse_healthcheck_rows(
            rows
        )

        all_records.extend(records)

    return all_records


def save_json(data, file_path):

    os.makedirs(
        os.path.dirname(file_path),
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


if __name__ == "__main__":

    input_file = (
        "data/case01_standard_healthcheck.pdf"
    )

    output_file = (
        "output/healthcheck.json"
    )

    print("Azure 분석 시작")

    result = analyze_layout(
        input_file
    )

    print("Azure 분석 완료")

    records = extract_healthcheck(
        result
    )

    mapped, unmapped = map_fields(
        records
    )

    output = {
        "healthcheck": mapped,
        "unmapped_fields": unmapped
    }

    save_json(
        output,
        output_file
    )

    print("\n추출 결과")

    for key, item in mapped.items():
        print(
            key,
            "=",
            item["value"],
            item["unit"]
        )

    print(
        "\n매핑되지 않은 항목:",
        len(unmapped)
    )

    print(
        "\nJSON 저장 완료:",
        output_file
    )