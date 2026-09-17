import os
import json

from OCR.azure_layout import process_healthcheck


# ==================================================
# 설정
# ==================================================

DATA_DIR = "data"

RESULT_FILE = "output/batch_test_result.json"


# ==================================================
# PDF 목록
# ==================================================

def get_pdf_files():

    files = []

    for filename in os.listdir(DATA_DIR):

        if filename.lower().endswith(".pdf"):

            files.append(
                os.path.join(
                    DATA_DIR,
                    filename
                )
            )

    return sorted(files)


# ==================================================
# 결과 검사
# ==================================================

def check_result(
    file_path,
    result
):

    healthcheck = result.get(
        "healthcheck",
        {}
    )

    validation_errors = result.get(
        "validation_errors",
        []
    )

    unmapped_fields = result.get(
        "unmapped_fields",
        []
    )

    pregnancy_info = result.get(
        "pregnancy_info",
        {}
    )

    # 최종적으로 반드시 존재해야 하는 canonical fields
    required_fields = [

        "height_cm",
        "weight_kg",
        "waist_cm",
        "bmi_kg_m2",

        "vision_left",
        "vision_right",

        "hearing_left",
        "hearing_right",

        "systolic_bp_mmhg",
        "diastolic_bp_mmhg",

        "health_exam_hemoglobin_g_dl",
        "hs_crp_mg_l",

        "fasting_glucose_mg_dl",
        "hba1c_pct",

        "total_cholesterol_mg_dl",
        "hdl_cholesterol_mg_dl",
        "triglycerides_mg_dl",
        "ldl_cholesterol_mg_dl",

        "ast_u_l",
        "alt_u_l",
        "ggt_u_l",

        "urine_protein_dipstick",

        "ferritin_ng_ml",
        "creatinine_mg_dl",
        "serum_folate_ng_ml",

        "body_temperature_c",
        "current_hemoglobin_g_dl",

        "pregnancy_status"
    ]

    missing_fields = [

        field
        for field in required_fields
        if field not in healthcheck
    ]

    # --------------------------------------------------
    # H01 ~ H26 source ID 확인
    #
    # H05/H06은 각각 좌우 2개로 분리
    # H24는 pregnancy_info에서 별도 관리
    # --------------------------------------------------

    expected_source_ids = {
        f"H{i:02d}"
        for i in range(1, 27)
        if i != 24
    }

    found_source_ids = set()

    for item in healthcheck.values():

        if not isinstance(
            item,
            dict
        ):
            continue

        source_id = item.get(
            "source_id"
        )

        if source_id:
            found_source_ids.add(
                source_id
            )

    missing_source_ids = sorted(
        expected_source_ids
        - found_source_ids
    )

    # --------------------------------------------------
    # 임신정보 확인
    # --------------------------------------------------

    pregnancy_status = (
        pregnancy_info.get(
            "status"
        )
    )

    pregnancy_ok = (
        pregnancy_status
        in [
            "pregnant",
            "not_pregnant"
        ]
    )

    # --------------------------------------------------
    # 최종 PASS / FAIL
    # --------------------------------------------------

    passed = (
        len(missing_fields) == 0
        and
        len(missing_source_ids) == 0
        and
        len(validation_errors) == 0
        and
        len(unmapped_fields) == 0
        and
        pregnancy_ok
    )

    return {

        "file":
            os.path.basename(
                file_path
            ),

        "patient_id":
            result.get(
                "patient_id"
            ),

        "status":
            "PASS"
            if passed
            else "FAIL",

        "healthcheck_field_count":
            len(healthcheck),

        "missing_fields":
            missing_fields,

        "missing_source_ids":
            missing_source_ids,

        "pregnancy":
            pregnancy_info,

        "validation_errors":
            validation_errors,

        "unmapped_fields":
            unmapped_fields
    }


# ==================================================
# Batch Test
# ==================================================

def run_batch_test():

    pdf_files = get_pdf_files()

    if not pdf_files:

        print(
            "data 폴더에 PDF가 없습니다."
        )

        return

    print("\n" + "=" * 60)
    print("MAMA Agent Batch OCR Test")
    print("=" * 60)

    print(
        f"\nPDF 개수: {len(pdf_files)}"
    )

    results = []

    for index, file_path in enumerate(
        pdf_files,
        start=1
    ):

        print("\n" + "-" * 60)

        print(
            f"[{index}/{len(pdf_files)}] "
            f"{os.path.basename(file_path)}"
        )

        try:

            output = process_healthcheck(
                file_path
            )

            test_result = check_result(
                file_path,
                output
            )

            results.append(
                test_result
            )

            print(
                "\n>>>",
                test_result["status"]
            )

            if test_result["missing_fields"]:

                print(
                    "누락 Field:",
                    test_result[
                        "missing_fields"
                    ]
                )

            if test_result["missing_source_ids"]:

                print(
                    "누락 H ID:",
                    test_result[
                        "missing_source_ids"
                    ]
                )

            if test_result["validation_errors"]:

                print(
                    "Validation:",
                    test_result[
                        "validation_errors"
                    ]
                )

            if test_result["unmapped_fields"]:

                print(
                    "Unmapped:",
                    test_result[
                        "unmapped_fields"
                    ]
                )

        except Exception as e:

            results.append({

                "file":
                    os.path.basename(
                        file_path
                    ),

                "status":
                    "ERROR",

                "error":
                    str(e)
            })

            print(
                "\n>>> ERROR:",
                e
            )

    # ==================================================
    # Summary
    # ==================================================

    pass_count = sum(
        1
        for result in results
        if result["status"] == "PASS"
    )

    fail_count = sum(
        1
        for result in results
        if result["status"] == "FAIL"
    )

    error_count = sum(
        1
        for result in results
        if result["status"] == "ERROR"
    )

    summary = {

        "total":
            len(results),

        "pass":
            pass_count,

        "fail":
            fail_count,

        "error":
            error_count,

        "results":
            results
    }

    os.makedirs(
        "output",
        exist_ok=True
    )

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 60)
    print("Batch Test Summary")
    print("=" * 60)

    print(
        "TOTAL :",
        len(results)
    )

    print(
        "PASS  :",
        pass_count
    )

    print(
        "FAIL  :",
        fail_count
    )

    print(
        "ERROR :",
        error_count
    )

    print(
        "\n결과 저장:",
        RESULT_FILE
    )


# ==================================================
# 실행
# ==================================================

if __name__ == "__main__":

    run_batch_test()