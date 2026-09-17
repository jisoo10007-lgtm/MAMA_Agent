import json
import os


GROUND_TRUTH_FILE = "data/ground_truth.json"
OUTPUT_DIR = "output"
RESULT_FILE = "output/accuracy_test_result.json"


# =========================================================
# 비교 대상 canonical fields
# =========================================================

HEALTHCHECK_FIELDS = [
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
]


# =========================================================
# JSON 로드
# =========================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# =========================================================
# OCR 결과 불러오기
# =========================================================

def load_patient_outputs():

    outputs = []

    if not os.path.exists(OUTPUT_DIR):
        return outputs

    for folder in os.listdir(OUTPUT_DIR):

        if not folder.startswith("P"):
            continue

        folder_path = os.path.join(
            OUTPUT_DIR,
            folder
        )

        if not os.path.isdir(folder_path):
            continue

        for filename in os.listdir(folder_path):

            if not filename.endswith(".json"):
                continue

            path = os.path.join(
                folder_path,
                filename
            )

            data = load_json(path)

            outputs.append(data)

    return outputs


# =========================================================
# 환자 연결
# =========================================================

def find_output(
    outputs,
    name,
    birth_date
):

    for output in outputs:

        patient_info = output.get(
            "patient_info",
            {}
        )

        if (
            patient_info.get("name") == name
            and
            patient_info.get("birth_date") == birth_date
        ):

            return output

    return None


# =========================================================
# 값 정규화
# =========================================================

def normalize_value(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower()

    # 청력
    if text in [
        "정상",
        "normal",
        "정상소견"
    ]:
        return "normal"

    if text in [
        "이상",
        "비정상",
        "abnormal"
    ]:
        return "abnormal"

    # 단백뇨
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

    # 숫자 문자열
    try:

        return float(
            text.replace(",", "")
        )

    except ValueError:

        return text


# =========================================================
# 값 비교
# =========================================================

def values_equal(
    expected,
    actual,
    tolerance=0.01
):

    expected = normalize_value(
        expected
    )

    actual = normalize_value(
        actual
    )

    if expected is None or actual is None:

        return expected is actual

    if (
        isinstance(expected, float)
        and
        isinstance(actual, float)
    ):

        return abs(
            expected - actual
        ) <= tolerance

    return expected == actual


# =========================================================
# OCR healthcheck 값 가져오기
# =========================================================

def get_actual_health_value(
    healthcheck,
    field
):

    item = healthcheck.get(
        field
    )

    if item is None:
        return None

    # OCR JSON 구조
    # "height_cm": {
    #     "value": 158.7,
    #     ...
    # }

    if isinstance(item, dict):

        return item.get(
            "value"
        )

    return item


# =========================================================
# 임신 상태 정규화
# =========================================================

def normalize_pregnancy_status(value):

    if value is None:
        return None

    text = str(value).strip().lower()

    if text in [
        "비임신",
        "not_pregnant",
        "not pregnant",
        "false"
    ]:
        return False

    if (
        text == "임신"
        or text == "pregnant"
        or text.startswith("임신(")
    ):
        return True

    return None


# =========================================================
# Accuracy Test
# =========================================================

def run_accuracy_test():

    if not os.path.exists(
        GROUND_TRUTH_FILE
    ):

        print(
            "ground_truth.json을 찾을 수 없습니다:"
        )

        print(
            GROUND_TRUTH_FILE
        )

        return

    ground_truth = load_json(
        GROUND_TRUTH_FILE
    )

    outputs = load_patient_outputs()

    print("\n" + "=" * 60)
    print("MAMA OCR Accuracy Test")
    print("=" * 60)

    print(
        f"\nGround Truth 문서: "
        f"{len(ground_truth)}"
    )

    print(
        f"OCR 결과 문서: "
        f"{len(outputs)}"
    )

    total = 0
    matched = 0
    mismatched = 0
    missing = 0

    field_stats = {
        field: {
            "total": 0,
            "matched": 0
        }
        for field in HEALTHCHECK_FIELDS
    }

    # 임신 상태 별도 통계
    pregnancy_stats = {
        "total": 0,
        "matched": 0
    }

    errors = []

    document_pass = 0
    document_fail = 0

    # =====================================================
    # 각 환자 비교
    # =====================================================

    for filename, truth in ground_truth.items():

        patient_info = truth.get(
            "patient_info",
            {}
        )

        name = patient_info.get(
            "name"
        )

        birth_date = patient_info.get(
            "birth_date"
        )

        print(
            f"\n[{filename}] "
            f"{name}"
        )

        output = find_output(
            outputs,
            name,
            birth_date
        )

        if output is None:

            print(
                "  -> FAIL: OCR 결과 없음"
            )

            document_fail += 1

            errors.append({
                "file": filename,
                "patient": name,
                "type": "OUTPUT_NOT_FOUND"
            })

            continue

        truth_healthcheck = truth.get(
            "healthcheck",
            {}
        )

        actual_healthcheck = output.get(
            "healthcheck",
            {}
        )

        document_errors = []

        # =================================================
        # Healthcheck 비교
        # =================================================

        for field in HEALTHCHECK_FIELDS:

            expected = truth_healthcheck.get(
                field
            )

            actual = get_actual_health_value(
                actual_healthcheck,
                field
            )

            total += 1

            field_stats[field][
                "total"
            ] += 1

            if actual is None:

                missing += 1

                error = {
                    "file": filename,
                    "patient": name,
                    "field": field,
                    "expected": expected,
                    "actual": None,
                    "type": "MISSING"
                }

                errors.append(error)
                document_errors.append(error)

                continue

            if values_equal(
                expected,
                actual
            ):

                matched += 1

                field_stats[field][
                    "matched"
                ] += 1

            else:

                mismatched += 1

                error = {
                    "file": filename,
                    "patient": name,
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                    "type": "MISMATCH"
                }

                errors.append(error)
                document_errors.append(error)

        # =================================================
        # Pregnancy 비교
        # =================================================

        truth_pregnancy = truth.get(
            "pregnancy",
            {}
        )

        actual_pregnancy = output.get(
            "pregnancy_info",
            {}
        )

        expected_pregnant = (
            truth_pregnancy.get(
                "is_pregnant"
            )
        )

        actual_status = (
            actual_pregnancy.get(
                "status"
            )
        )

        actual_pregnant = (
            normalize_pregnancy_status(
                actual_status
            )
        )

        total += 1

        pregnancy_stats[
            "total"
        ] += 1

        if (
            expected_pregnant
            == actual_pregnant
        ):

            matched += 1

            pregnancy_stats[
                "matched"
            ] += 1

        else:

            mismatched += 1

            error = {
                "file": filename,
                "patient": name,
                "field":
                    "pregnancy.is_pregnant",
                "expected":
                    expected_pregnant,
                "actual":
                    actual_pregnant,
                "type":
                    "MISMATCH"
            }

            errors.append(error)
            document_errors.append(error)

        # =================================================
        # 임신 주수 비교
        # =================================================

        expected_week = (
            truth_pregnancy.get(
                "gestational_week"
            )
        )

        actual_week = (
            actual_pregnancy.get(
                "gestational_weeks"
            )
        )

        total += 1

        if values_equal(
            expected_week,
            actual_week
        ):

            matched += 1

        else:

            mismatched += 1

            error = {
                "file": filename,
                "patient": name,
                "field":
                    "pregnancy.gestational_week",
                "expected":
                    expected_week,
                "actual":
                    actual_week,
                "type":
                    "MISMATCH"
            }

            errors.append(error)
            document_errors.append(error)

        # =================================================
        # 문서 PASS / FAIL
        # =================================================

        if not document_errors:

            document_pass += 1

            print(
                "  -> PASS"
            )

        else:

            document_fail += 1

            print(
                f"  -> FAIL "
                f"({len(document_errors)} errors)"
            )


    # =====================================================
    # Accuracy
    # =====================================================

    accuracy = (
        matched / total * 100
        if total > 0
        else 0
    )

    print("\n" + "=" * 60)
    print("Accuracy Summary")
    print("=" * 60)

    print(
        f"Documents : "
        f"{len(ground_truth)}"
    )

    print(
        f"Doc PASS  : "
        f"{document_pass}"
    )

    print(
        f"Doc FAIL  : "
        f"{document_fail}"
    )

    print(
        f"Compared  : "
        f"{total}"
    )

    print(
        f"Matched   : "
        f"{matched}"
    )

    print(
        f"Mismatch  : "
        f"{mismatched}"
    )

    print(
        f"Missing   : "
        f"{missing}"
    )

    print(
        f"Accuracy  : "
        f"{accuracy:.2f}%"
    )


    # =====================================================
    # Field Accuracy
    # =====================================================

    print("\nField Accuracy")
    print("-" * 60)

    for field in HEALTHCHECK_FIELDS:

        stats = field_stats[
            field
        ]

        print(
            f"{field:<35} "
            f"{stats['matched']}"
            f"/"
            f"{stats['total']}"
        )

    print(
        f"{'pregnancy.is_pregnant':<35} "
        f"{pregnancy_stats['matched']}"
        f"/"
        f"{pregnancy_stats['total']}"
    )


    # =====================================================
    # 오류 상세
    # =====================================================

    if errors:

        print("\n오류 상세")
        print("-" * 60)

        for error in errors:

            print(
                error
            )

    else:

        print(
            "\n모든 OCR 값이 Ground Truth와 일치합니다."
        )


    # =====================================================
    # 결과 저장
    # =====================================================

    result = {

        "documents":
            len(ground_truth),

        "document_pass":
            document_pass,

        "document_fail":
            document_fail,

        "compared":
            total,

        "matched":
            matched,

        "mismatch":
            mismatched,

        "missing":
            missing,

        "accuracy_pct":
            round(
                accuracy,
                2
            ),

        "field_stats":
            field_stats,

        "pregnancy_stats":
            pregnancy_stats,

        "errors":
            errors
    }

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\n결과 저장:",
        RESULT_FILE
    )


# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":

    run_accuracy_test()