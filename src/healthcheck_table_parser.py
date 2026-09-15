def table_to_rows(table):
    """
    Azure Table 객체를
    2차원 리스트로 변환한다.
    """

    rows = [
        [""] * table.column_count
        for _ in range(table.row_count)
    ]

    for cell in table.cells:

        rows[
            cell.row_index
        ][
            cell.column_index
        ] = cell.content.strip()

    return rows


def parse_healthcheck_rows(rows):
    """
    MAMA 여성건강센터 건강검진 결과표 파싱.

    예상 구조:
    구분 | 검사항목 | 결과 | 단위 | 참고치
    """

    records = []

    for row in rows:

        if len(row) < 4:
            continue

        category = row[0].strip()
        name = row[1].strip()
        value = row[2].strip()
        unit = row[3].strip()

        # Header 제외
        if name in [
            "",
            "검사항목",
            "검사명",
            "항목"
        ]:
            continue

        # 값이 없는 행 제외
        if not value:
            continue

        records.append({
            "category": category,
            "name": name,
            "value": value,
            "unit": unit
        })

    return records