def table_to_rows(table):
    rows = [
        [""] * table.column_count
        for _ in range(table.row_count)
    ]

    for cell in table.cells:
        rows[cell.row_index][cell.column_index] = cell.content.strip()

    return rows


def parse_healthcheck_rows(rows):
    """
    3열 구조:
    검사항목 | 결과 | 단위

    6열 구조:
    검사항목 | 결과 | 단위 | 검사항목 | 결과 | 단위

    둘 다 처리한다.
    """

    extracted = []

    for row in rows:
        if len(row) < 3:
            continue

        # 왼쪽 3열
        left = row[:3]
        item = make_record(left)

        if item:
            extracted.append(item)

        # 오른쪽 3열
        if len(row) >= 6:
            right = row[3:6]
            item = make_record(right)

            if item:
                extracted.append(item)

    return extracted


def make_record(columns):
    name = columns[0].strip()
    value = columns[1].strip()
    unit = columns[2].strip()

    # 헤더 제거
    if name in [
        "",
        "검사항목",
        "항목",
        "검사명"
    ]:
        return None

    if not value:
        return None

    return {
        "name": name,
        "value": value,
        "unit": unit
    }