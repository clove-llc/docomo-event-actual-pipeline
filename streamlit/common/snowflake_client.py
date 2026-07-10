import streamlit as st
from typing import Any

# ====================
# 共通接続設定
# ====================


def _quote_ident(name: str) -> str:
    """Snowflake識別子をダブルクォートする。"""
    return '"' + name.replace('"', '""') + '"'


def _current_database(*, session=None, conn=None) -> str:
    """現在の接続コンテキストから database を取得。"""
    rows = fetch_all(
        "SELECT CURRENT_DATABASE()",
        session=session,
        conn=conn,
    )

    db = rows[0][0]

    if not db:
        raise RuntimeError("database を取得できませんでした。")

    return str(db)


def _get_session():
    """Streamlit in Snowflake なら Snowpark session、ローカルなら None。"""
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:  # noqa: BLE001
        return None


def table_name(
    table: str,
    *,
    schema: str,
    database: str,
    session=None,
    conn=None,
) -> str:
    db = database or _current_database(session=session, conn=conn)

    return ".".join(
        [
            _quote_ident(db),
            _quote_ident(schema),
            _quote_ident(table),
        ]
    )


# ====================
# 共通接続設定
# ====================
session = _get_session()
conn = None if session else st.connection("snowflake")


# ====================
# クエリ実行系
# ====================


def fetch_all(
    sql: str,
    params: list[Any] | None = None,
    *,
    session=None,
    conn=None,
) -> list[tuple[Any, ...]]:
    """SiS / ローカル共通の SELECT 実行。"""
    if session is not None:
        q = session.sql(sql, params=params) if params else session.sql(sql)
        return [tuple(row) for row in q.collect()]

    if conn is None:
        raise ValueError("session または conn が必要です。")

    cur = conn.cursor()
    try:
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchall() if cur.description else []
    finally:
        cur.close()


def fetch_current_database_name() -> str:
    return _current_database(session=session, conn=conn)


def fetch_schema_names() -> list[str]:
    db = _current_database(session=session, conn=conn)

    rows = fetch_all(
        f"""
        SELECT
            SCHEMA_NAME
        FROM {_quote_ident(db)}.INFORMATION_SCHEMA.SCHEMATA
        WHERE SCHEMA_NAME <> 'INFORMATION_SCHEMA'
        ORDER BY SCHEMA_NAME
        """,
        session=session,
        conn=conn,
    )

    return [str(row[0]) for row in rows]


def execute_sql(
    sql: str,
    params: list[Any] | tuple[Any, ...] | None = None,
    *,
    session=None,
    conn=None,
) -> None:
    if session is not None:
        q = session.sql(sql, params=params) if params else session.sql(sql)
        q.collect()
        return

    if conn is None:
        raise ValueError("session または conn が必要です。")

    with conn.cursor() as cursor:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)


def execute_many(
    sql: str,
    params_list: list[tuple[Any, ...]],
    *,
    session=None,
    conn=None,
) -> None:
    if not params_list:
        return

    if session is not None:
        for params in params_list:
            session.sql(sql, params=params).collect()
        return

    if conn is None:
        raise ValueError("session または conn が必要です。")

    with conn.cursor() as cursor:
        cursor.executemany(sql, params_list)
