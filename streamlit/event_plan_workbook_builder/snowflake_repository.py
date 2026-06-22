from __future__ import annotations
import streamlit as st

from typing import Any, cast

from config import SNOWFLAKE_CACHE_TTL_SECONDS
from entities import DateDetail, FacilityDailyTargetDetail
from utils import to_date


def _fetch_all(
    sql: str,
    params: list[Any] | None = None,
) -> list[tuple[Any, ...]]:
    conn = st.connection("snowflake")

    with conn.cursor() as cursor:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)

        return cast(list[tuple[Any, ...]], cursor.fetchall())


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_benchmark_period_keys() -> list[str]:
    """Snowflakeから過去実績対象期間の一覧を取得する。"""
    conn = st.connection("snowflake")

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                BENCHMARK_PERIOD_KEY
            FROM INT.INT_BENCHMARK_PERIODS
            ORDER BY BENCHMARK_PERIOD_KEY DESC
            """)
        rows = cursor.fetchall()

    return [str(row[0]) for row in rows]


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_facility_daily_target_details(
    benchmark_period_key: str,
    year: int,
    month: int,
    regional_office_name: str,
) -> list[FacilityDailyTargetDetail]:
    """Snowflakeから過去実績対象期間の実績をもとに算出された対象支社の目標値を取得する。"""
    rows = _fetch_all(
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
        WHERE BENCHMARK_PERIOD_KEY = ?
          AND EXTRACT(YEAR FROM DATE) = ?
          AND EXTRACT(MONTH FROM DATE) = ?
          AND REGIONAL_OFFICE = ?
          AND HAS_TARGET_CPA
        """,
        [
            benchmark_period_key,
            year,
            month,
            regional_office_name,
        ],
    )

    return [
        FacilityDailyTargetDetail(
            facility_code=int(row[0]),
            facility_name=str(row[1]),
            po_level=str(row[2]),
            regional_office=str(row[3]),
            branch_office=str(row[4]),
            date=to_date(row[5]),
            date_flag=str(row[6]),
            cpa=int(row[7]),
            is_excluded=bool(row[8]),
            target_value=int(row[9]),
        )
        for row in rows
    ]


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_date_master(year: int, month: int) -> list[DateDetail]:
    """Snowflakeから指定された年月の日付マスタ情報を取得する。"""
    rows = _fetch_all(
        """
        SELECT
            DATE,
            WEEKDAY_NAME_AND_WEEK_NUMBER_MONTHLY,
            DATE_FLAG
        FROM STG.STG_DATE_MASTER
        WHERE YEAR = ?
          AND MONTH = ?
        ORDER BY DATE
        """,
        [
            year,
            month,
        ],
    )

    return [
        DateDetail(
            date=to_date(row[0]),
            weekday_name_and_week_number_monthly=str(row[1]),
            date_flag=str(row[2]),
        )
        for row in rows
    ]
