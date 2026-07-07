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


def apply_benchmark_period_changes(
    before_periods: list[BenchmarkPeriod],
    after_periods: list[BenchmarkPeriod],
) -> dict[str, int]:
    """Snowflakeの基準期間マスタに追加・更新・削除を反映する。"""
    before_by_key = {period.benchmark_period_key: period for period in before_periods}
    after_by_key = {period.benchmark_period_key: period for period in after_periods}

    before_keys = set(before_by_key.keys())
    after_keys = set(after_by_key.keys())

    insert_keys = after_keys - before_keys
    delete_keys = before_keys - after_keys
    maybe_update_keys = before_keys & after_keys

    update_keys = [
        key for key in maybe_update_keys if before_by_key[key] != after_by_key[key]
    ]

    delete_rows = [(key,) for key in delete_keys]

    insert_rows = [
        (
            after_by_key[key].benchmark_period_key,
            after_by_key[key].benchmark_period_name,
            after_by_key[key].period_start_date.isoformat(),
            after_by_key[key].period_end_date.isoformat(),
            after_by_key[key].period_month_count,
        )
        for key in insert_keys
    ]

    update_rows = [
        (
            after_by_key[key].benchmark_period_name,
            after_by_key[key].period_start_date.isoformat(),
            after_by_key[key].period_end_date.isoformat(),
            after_by_key[key].period_month_count,
            after_by_key[key].benchmark_period_key,
        )
        for key in update_keys
    ]

    conn = st.connection("snowflake")

    with conn.cursor() as cursor:
        try:
            cursor.execute("BEGIN")

            if delete_rows:
                cursor.executemany(
                    """
                    DELETE FROM RAW.RAW_BENCHMARK_PERIODS
                    WHERE BENCHMARK_PERIOD_KEY = ?
                    """,
                    delete_rows,
                )

            if update_rows:
                cursor.executemany(
                    """
                    UPDATE RAW.RAW_BENCHMARK_PERIODS
                    SET
                        BENCHMARK_PERIOD_NAME = ?,
                        PERIOD_START_DATE = ?,
                        PERIOD_END_DATE = ?,
                        PERIOD_MONTH_COUNT = ?
                    WHERE BENCHMARK_PERIOD_KEY = ?
                    """,
                    update_rows,
                )

            if insert_rows:
                cursor.executemany(
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
                    insert_rows,
                )

            cursor.execute("COMMIT")

        except Exception:
            cursor.execute("ROLLBACK")
            raise

    return {
        "inserted": len(insert_rows),
        "updated": len(update_rows),
        "deleted": len(delete_rows),
    }


def clear_benchmark_periods_cache() -> None:
    fetch_benchmark_periods.clear()
