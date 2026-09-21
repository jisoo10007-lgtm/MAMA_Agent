import json
import os
from typing import Any

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


load_dotenv()

CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)
CONTAINER_NAME = os.getenv(
    "AZURE_STORAGE_CONTAINER",
    "mama-health-data",
)


def _get_container_client():
    if not CONNECTION_STRING:
        raise ValueError(
            "AZURE_STORAGE_CONNECTION_STRING이 설정되지 않았습니다."
        )

    blob_service_client = BlobServiceClient.from_connection_string(
        CONNECTION_STRING
    )

    return blob_service_client.get_container_client(
        CONTAINER_NAME
    )


def upload_pdf(
    file_path: str,
    patient_id: str,
    exam_date: str,
) -> str:
    container_client = _get_container_client()

    blob_name = (
        f"raw/{patient_id}/"
        f"healthcheck_{exam_date}.pdf"
    )

    with open(file_path, "rb") as file:
        container_client.upload_blob(
            name=blob_name,
            data=file,
            overwrite=True,
        )

    return blob_name


def upload_json(
    data: dict[str, Any],
    patient_id: str,
    exam_date: str,
) -> str:
    container_client = _get_container_client()

    blob_name = (
        f"processed/{patient_id}/"
        f"healthcheck_{exam_date}.json"
    )

    json_data = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    container_client.upload_blob(
        name=blob_name,
        data=json_data.encode("utf-8"),
        overwrite=True,
    )

    return blob_name

def download_json(
    blob_name: str,
) -> dict | list | None:
    container_client = _get_container_client()
    blob_client = container_client.get_blob_client(
        blob_name
    )

    try:
        data = blob_client.download_blob().readall()

        return json.loads(
            data.decode("utf-8")
        )

    except Exception as e:
        # 아직 파일이 없는 최초 실행
        if "BlobNotFound" in str(e):
            return None

        raise


def upload_metadata_json(
    data: dict | list,
    blob_name: str,
) -> str:
    container_client = _get_container_client()

    json_data = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    container_client.upload_blob(
        name=blob_name,
        data=json_data.encode("utf-8"),
        overwrite=True,
    )

    return blob_name