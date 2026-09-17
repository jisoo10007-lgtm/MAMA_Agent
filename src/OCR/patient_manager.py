import json
import os
import re
from datetime import datetime


PATIENT_INDEX_FILE = (
    "output/patient_index.json"
)


def normalize_birth_date(value):

    if not value:
        return None

    numbers = re.sub(
        r"\D",
        "",
        value
    )

    if len(numbers) != 8:
        return None

    try:

        date = datetime.strptime(
            numbers,
            "%Y%m%d"
        )

        return date.strftime(
            "%Y-%m-%d"
        )

    except ValueError:

        return None


def load_patient_index():

    if not os.path.exists(
        PATIENT_INDEX_FILE
    ):
        return []

    with open(
        PATIENT_INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_patient_index(
    patients
):

    os.makedirs(
        "output",
        exist_ok=True
    )

    with open(
        PATIENT_INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            patients,
            f,
            ensure_ascii=False,
            indent=2
        )


def generate_patient_id(
    patients
):

    if not patients:
        return "P000001"

    numbers = []

    for patient in patients:

        patient_id = patient.get(
            "patient_id",
            ""
        )

        match = re.match(
            r"P(\d+)",
            patient_id
        )

        if match:

            numbers.append(
                int(
                    match.group(1)
                )
            )

    if not numbers:
        return "P000001"

    next_number = (
        max(numbers) + 1
    )

    return (
        f"P{next_number:06d}"
    )


def get_or_create_patient_id(
    name,
    birth_date
):

    birth_date = (
        normalize_birth_date(
            birth_date
        )
    )

    if not name:

        raise ValueError(
            "환자 이름이 없습니다."
        )

    if not birth_date:

        raise ValueError(
            "생년월일이 올바르지 않습니다."
        )

    patients = load_patient_index()

    # 기존 환자 확인
    for patient in patients:

        if (
            patient["name"] == name
            and
            patient["birth_date"]
            == birth_date
        ):

            return patient[
                "patient_id"
            ]

    # 신규 환자
    patient_id = (
        generate_patient_id(
            patients
        )
    )

    patients.append({
        "patient_id":
            patient_id,

        "name":
            name,

        "birth_date":
            birth_date
    })

    save_patient_index(
        patients
    )

    return patient_id