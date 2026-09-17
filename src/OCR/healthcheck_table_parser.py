def table_to_rows(table):
    """
    Azure Document Intelligence Table 객체를
    2차원 리스트로 변환한다.
    """

    rows = [
        [""] * table.column_count
        for _ in range(table.row_count)
    ]

    for cell in table.cells:

        content = cell.content or ""

        rows[
            cell.row_index
        ][
            cell.column_index
        ] = content.strip()

    return rows


def parse_healthcheck_rows(rows):
    """
    MAMA 최종 건강검진표 파싱.

    구조:
    ID | 검사항목 | 결과 | 단위 | 비고

    예:
    H07 | 수축기 혈압(SBP) | 118 | mmHg | -
    """

    records = []

    for row in rows:

        if len(row) < 4:
            continue

        item_id = row[0].strip()
        name = row[1].strip()
        value = row[2].strip()
        unit = row[3].strip()

        note = ""

        if len(row) >= 5:
            note = row[4].strip()

        # Header 제외
        if (
            item_id in ["ID", "Id", "id"]
            or name in [
                "",
                "검사항목",
                "검사명",
                "항목"
            ]
        ):
            continue

        # H01 ~ H26만 검사 항목으로 인정
        if not item_id.upper().startswith("H"):
            continue

        # 값 없는 행 제외
        if not value:
            continue

        records.append({
            "item_id": item_id.upper(),
            "name": name,
            "value": value,
            "unit": unit,
            "note": note
        })

    return records