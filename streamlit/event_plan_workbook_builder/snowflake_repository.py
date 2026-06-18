from __future__ import annotations
import pandas as pd
import snowflake.connector
import streamlit as st

from typing import Any

from config import SNOWFLAKE_CACHE_TTL_SECONDS


def _connect():
    snowflake_config = dict(st.secrets["snowflake"])
    return snowflake.connector.connect(**snowflake_config)


def _fetch_pandas_all(sql: str, params: dict[str, Any] | None) -> pd.DataFrame:
    conn = _connect()

    try:
        cursor = conn.cursor()
        try:
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            return cursor.fetch_pandas_all()
        finally:
            cursor.close()
    finally:
        conn.close()


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_benchmark_period_keys() -> list[str]:
    """Snowflakeから過去実績対象期間の一覧を取得する。"""

    conn = _connect()

    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT
                    BENCHMARK_PERIOD_KEY
                FROM INT.INT_BENCHMARK_PERIODS
                ORDER BY BENCHMARK_PERIOD_KEY DESC
                """)
            rows = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()

    return [str(row[0]) for row in rows]


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_facility_targets(
    benchmark_period_key: str,
    year: int,
    month: int,
    regional_office_name: str,
) -> pd.DataFrame:
    """Snowflakeから過去実績対象期間の実績をもとに算出された対象支社の目標値を取得する。"""
    return _fetch_pandas_all(
        """
        SELECT
            FACILITY_CODE,
            FACILITY_NAME,
            PO_LEVEL,
            REGIONAL_OFFICE,
            BRANCH_OFFICE,
            DATE,
            DATE_FLAG,
            CPA,
            IS_EXCLUDED,
            STANDARD_TARGET_SEASONAL
        FROM MART.FACT_FACILITY_PERFORMANCE_SLOTS
        WHERE BENCHMARK_PERIOD_KEY = %(benchmark_period_key)s
          AND EXTRACT(YEAR FROM DATE) = %(year)s
          AND EXTRACT(MONTH FROM DATE) = %(month)s
          AND REGIONAL_OFFICE = %(regional_office_name)s
          AND HAS_TARGET_CPA
        """,
        {
            "benchmark_period_key": benchmark_period_key,
            "year": year,
            "month": month,
            "regional_office_name": regional_office_name,
        },
    )


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_date_master(year: int, month: int) -> pd.DataFrame:
    """Snowflakeから指定された年月の日付マスタ情報を取得する。"""
    return _fetch_pandas_all(
        """
        SELECT
            DATE,
            WEEKDAY_NAME_AND_WEEK_NUMBER_MONTHLY,
            DATE_FLAG
        FROM STG.STG_DATE_MASTER
        WHERE YEAR = %(year)s
          AND MONTH = %(month)s
        ORDER BY DATE
        """,
        {
            "year": year,
            "month": month,
        },
    )
