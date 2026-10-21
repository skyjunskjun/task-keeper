from sqlalchemy import event


def _count_selects(client, db_session) -> int:
    # GET /tasks 동안 실행된 SELECT 쿼리 수를 셉니다.
    selects: list[str] = []
    engine = db_session.get_bind()

    def count(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        res = client.get("/tasks")
    finally:
        event.remove(engine, "before_cursor_execute", count)

    assert res.status_code == 200
    return len(selects)


def test_list_tasks_query_count_is_constant(client, db_session):
    client.post("/tasks", json={"title": "할 일 0", "tags": ["t0"]})
    one_task = _count_selects(client, db_session)

    for i in range(1, 10):
        client.post("/tasks", json={"title": f"할 일 {i}", "tags": [f"t{i}"]})
    ten_tasks = _count_selects(client, db_session)

    # tasks 1번 + tags IN 1번. 할 일 수가 늘어도 쿼리 수는 그대로여야 합니다(N+1 방지).
    assert one_task == 2
    assert ten_tasks == 2
