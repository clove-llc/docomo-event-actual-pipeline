from __future__ import annotations

import datetime
import streamlit as st

from datetime import date
from typing import Any, cast
from config import SNOWFLAKE_CACHE_TTL_SECONDS
from entities import BenchmarkPeriod


def to_date(value: Any) -> date:
    if isinstance(value, datetime.datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


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


def init_table() -> None:
    """Snowflakeに基準期間マスタのテーブルを作成する。"""
    conn = st.connection("snowflake")

    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RAW.RAW_BENCHMARK_PERIODS (
                BENCHMARK_PERIOD_KEY STRING,
                BENCHMARK_PERIOD_NAME STRING,
                PERIOD_START_DATE DATE,
                PERIOD_END_DATE DATE,
                PERIOD_MONTH_COUNT INT
            )
            """)


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_benchmark_periods() -> list[BenchmarkPeriod]:
    """Snowflakeから基準期間マスタを取得する。"""
    rows = _fetch_all("""
        SELECT
            BENCHMARK_PERIOD_KEY,
            BENCHMARK_PERIOD_NAME,
            PERIOD_START_DATE,
            PERIOD_END_DATE,
            PERIOD_MONTH_COUNT
        FROM RAW.RAW_BENCHMARK_PERIODS
        ORDER BY
            PERIOD_START_DATE,
            PERIOD_END_DATE,
            BENCHMARK_PERIOD_KEY
        """)

    return [
        BenchmarkPeriod(
            benchmark_period_key=str(row[0]),
            benchmark_period_name=str(row[1]),
            period_start_date=to_date(row[2]),
            period_end_date=to_date(row[3]),
            period_month_count=int(row[4]),
        )
        for row in rows
    ]


def insert_benchmark_period(benchmark_period: BenchmarkPeriod) -> None:
    """Snowflakeに基準期間マスタを追加する。"""
    conn = st.connection("snowflake")

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO RAW.RAW_BENCHMARK_PERIODS (
                BENCHMARK_PERIOD_KEY,
                BENCHMARK_PERIOD_NAME,
                PERIOD_START_DATE,
                PERIOD_END_DATE,
                PERIOD_MONTH_COUNT
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                benchmark_period.benchmark_period_key,
                benchmark_period.benchmark_period_name,
                benchmark_period.period_start_date,
                benchmark_period.period_end_date,
                benchmark_period.period_month_count,
            ],
        )


def apply_benchmark_period_updates_and_deletes(
    update_rows: list[tuple[str, BenchmarkPeriod]],
    delete_keys: list[str],
) -> dict[str, int]:
    """Snowflakeの基準期間マスタに更新・削除を反映する。INSERTは行わない。"""
    conn = st.connection("snowflake")

    update_params = [
        (
            period.benchmark_period_key,
            period.benchmark_period_name,
            period.period_start_date.isoformat(),
            period.period_end_date.isoformat(),
            period.period_month_count,
            original_benchmark_period_key,
        )
        for original_benchmark_period_key, period in update_rows
    ]

    delete_params = [(benchmark_period_key,) for benchmark_period_key in delete_keys]

    with conn.cursor() as cursor:
        try:
            cursor.execute("BEGIN")

            if delete_params:
                cursor.executemany(
                    """
                    DELETE FROM RAW.RAW_BENCHMARK_PERIODS
                    WHERE BENCHMARK_PERIOD_KEY = ?
                    """,
                    delete_params,
                )

            if update_params:
                cursor.executemany(
                    """
                    UPDATE RAW.RAW_BENCHMARK_PERIODS
                    SET
                        BENCHMARK_PERIOD_KEY = ?,
                        BENCHMARK_PERIOD_NAME = ?,
                        PERIOD_START_DATE = ?,
                        PERIOD_END_DATE = ?,
                        PERIOD_MONTH_COUNT = ?
                    WHERE BENCHMARK_PERIOD_KEY = ?
                    """,
                    update_params,
                )

            cursor.execute("COMMIT")

        except Exception:
            cursor.execute("ROLLBACK")
            raise

    return {
        "updated": len(update_params),
        "deleted": len(delete_params),
    }


def clear_benchmark_periods_cache() -> None:
    fetch_benchmark_periods.clear()
