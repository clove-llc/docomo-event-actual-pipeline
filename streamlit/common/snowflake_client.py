import streamlit as st
from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionSetting:
    database_name: str
    schema_name: str


# ====================
# 共通接続設定
# ====================


def _quote_ident(name: str) -> str:
    """Snowflake識別子をダブルクォートする。"""
    return '"' + name.replace('"', '""') + '"'


def _get_session():
    """Streamlit in Snowflake なら Snowpark session、ローカルなら None。"""
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:  # noqa: BLE001
        return None


def table_name(
    table_name: str,
    *,
    schema_name: str,
    database_name: str,
    session=None,
    conn=None,
) -> str:
    return ".".join(
        [
            _quote_ident(database_name),
            _quote_ident(schema_name),
            _quote_ident(table_name),
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


def fetch_database_names() -> list[str]:
    execute_sql(
        f"SHOW DATABASES",
        session=session,
        conn=conn,
    )

    rows = fetch_all(
        """
        SELECT "name"
        FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        ORDER BY LOWER("name")
        """,
        session=session,
        conn=conn,
    )

    return [str(row[0]) for row in rows]


def fetch_schema_names(database_name: str) -> list[str]:
    quoted_database_name = _quote_ident(database_name)

    execute_sql(
        f"SHOW SCHEMAS IN DATABASE {quoted_database_name}",
        session=session,
        conn=conn,
    )

    rows = fetch_all(
        """
        SELECT "name"
        FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        ORDER BY LOWER("name")
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
