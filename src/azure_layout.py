import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient


load_dotenv()

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

if not endpoint:
    raise ValueError("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT가 없습니다.")

if not key:
    raise ValueError("AZURE_DOCUMENT_INTELLIGENCE_KEY가 없습니다.")


client = DocumentIntelligenceClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)


def analyze_layout(file_path: str):
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=f
        )

    result = poller.result()
    return result


if __name__ == "__main__":
    file_path = "data/case01_standard_healthcheck.pdf"

    result = analyze_layout(file_path)

    print("분석 완료")
    print("페이지 수:", len(result.pages))
    print("테이블 수:", len(result.tables))

print("\n=== OCR TEXT ===")

for page_index, page in enumerate(result.pages, start=1):
    print(f"\n[PAGE {page_index}]")

    if page.lines:
        for line in page.lines:
            print(line.content)

print("\n=== TABLES ===")

for table_index, table in enumerate(result.tables, start=1):
    print(f"\n[TABLE {table_index}]")
    print("rows:", table.row_count)
    print("columns:", table.column_count)

    for cell in table.cells:
        print(
            f"row={cell.row_index}, "
            f"col={cell.column_index}, "
            f"text={cell.content}"
        )