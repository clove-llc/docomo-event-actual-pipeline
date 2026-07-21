"""Snowflake 接続まわりの共通ヘルパー（ローカル / Streamlit in Snowflake 両対応）。"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def get_active_session():
    """SiS のアクティブセッション。ローカルでは None。"""
    try:
        from snowflake.snowpark.context import get_active_session as _gas

        return _gas()
    except Exception:  # noqa: BLE001
        return None


def get_sf_config() -> dict | None:
    """ローカル実行時の接続情報（.streamlit/secrets.toml [snowflake]）。"""
    try:
        return dict(st.secrets["snowflake"])
    except Exception:  # noqa: BLE001
        return None


def connect_snowflake(
    cfg: dict, database: str = "", schema: str = "", warehouse: str = ""
):
    """ローカル: snowflake.connector で外部接続。"""
    import snowflake.connector

    params = {}
    for key in (
        "account",
        "user",
        "password",
        "role",
        "authenticator",
        "private_key_file",
        "private_key_file_pwd",
        "host",
    ):
        if cfg.get(key):
            params[key] = cfg[key]
    params["warehouse"] = warehouse or cfg.get("warehouse")
    params["database"] = database or cfg.get("database")
    params["schema"] = schema or cfg.get("schema")
    return snowflake.connector.connect(**{k: v for k, v in params.items() if v})


def exec_sql(sql: str, *, session=None, conn=None):
    """SQL 実行（SiS はセッション、ローカルは connector）。"""
    if session is not None:
        return session.sql(sql).collect()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall() if cur.description else None
    cur.close()
    return rows


def load_dataframe(
    df: pd.DataFrame, table: str, database: str, schema: str, *, session=None, conn=None
):
    """既存テーブル（事前に CREATE 済み）へ DataFrame を追記ロード。

    列名は日本語・日付（ハイフン）を含むため quote_identifiers=True で厳密一致させる。
    """
    if session is not None:
        session.write_pandas(
            df,
            table,
            database=database or None,
            schema=schema or None,
            auto_create_table=False,
            overwrite=False,
            quote_identifiers=True,
        )
    else:
        from snowflake.connector.pandas_tools import write_pandas

        write_pandas(
            conn,
            df,
            table,
            database=database or None,
            schema=schema or None,
            auto_create_table=False,
            overwrite=False,
            quote_identifiers=True,
        )
