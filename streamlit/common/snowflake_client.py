import streamlit as st
from typing import Any

# ====================
# 共通接続設定
# ====================


def _get_session():
    """Streamlit in Snowflake なら Snowpark session、ローカルなら None。"""
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:  # noqa: BLE001
        return None


session = _get_session()
conn = None if session else st.connection("snowflake")


# ====================
# クエリ実行系
# ====================


def fetch_all(sql: str, params: list[Any] | None = None) -> list[tuple[Any, ...]]:
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


def execute_sql(
    sql: str,
    params: list[Any] | tuple[Any, ...] | None = None,
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
