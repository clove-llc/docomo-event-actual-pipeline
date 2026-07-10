from __future__ import annotations

import datetime
import streamlit as st

from datetime import date
from typing import Any
from config import SNOWFLAKE_CACHE_TTL_SECONDS
from entities import BenchmarkPeriod
from common.connection_settings import ConnectionSettings
from common.snowflake_client import (
    session,
    conn,
    table_name,
    fetch_all,
    execute_sql,
    execute_many,
)


def to_date(value: Any) -> date:
    if isinstance(value, datetime.datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


# ====================
# Snowflake からのデータ取得
# ====================


def clear_snowflake_cache() -> None:
    """Snowflake取得系のキャッシュをクリアする。"""
    fetch_benchmark_periods.clear()


def init_table(connection_settings: ConnectionSettings) -> None:
    target_table = table_name(
        "RAW_BENCHMARK_PERIODS",
        database=connection_settings.database_name,
        schema=connection_settings.raw_schema,
    )

    execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {target_table} (
            BENCHMARK_PERIOD_KEY STRING NOT NULL,
            BENCHMARK_PERIOD_NAME STRING NOT NULL,
            PERIOD_START_DATE DATE NOT NULL,
            PERIOD_END_DATE DATE NOT NULL,
            PERIOD_MONTH_COUNT INT NOT NULL
        )
        """,
        session=session,
        conn=conn,
    )


@st.cache_data(ttl=SNOWFLAKE_CACHE_TTL_SECONDS)
def fetch_benchmark_periods(
    connection_settings: ConnectionSettings,
) -> list[BenchmarkPeriod]:
    """Snowflakeから基準期間マスタを取得する。"""
    target_table = table_name(
        "RAW_BENCHMARK_PERIODS",
        database=connection_settings.database_name,
        schema=connection_settings.raw_schema,
        session=session,
        conn=conn,
    )

    rows = fetch_all(
        f"""
        SELECT
            BENCHMARK_PERIOD_KEY,
            BENCHMARK_PERIOD_NAME,
            PERIOD_START_DATE,
            PERIOD_END_DATE,
            PERIOD_MONTH_COUNT
        FROM {target_table}
        ORDER BY
            PERIOD_START_DATE,
            PERIOD_END_DATE,
            BENCHMARK_PERIOD_KEY
        """,
        [],
        session=session,
        conn=conn,
    )

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


def insert_benchmark_period(
    connection_settings: ConnectionSettings,
    benchmark_period: BenchmarkPeriod,
) -> None:
    target_table = table_name(
        "RAW_BENCHMARK_PERIODS",
        database=connection_settings.database_name,
        schema=connection_settings.raw_schema,
    )

    execute_sql(
        f"""
        INSERT INTO {target_table} (
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
            benchmark_period.period_start_date.isoformat(),
            benchmark_period.period_end_date.isoformat(),
            benchmark_period.period_month_count,
        ],
        session=session,
        conn=conn,
    )


def apply_benchmark_period_updates_and_deletes(
    connection_settings: ConnectionSettings,
    update_rows: list[tuple[str, BenchmarkPeriod]],
    delete_keys: list[str],
) -> dict[str, int]:
    target_table = table_name(
        "RAW_BENCHMARK_PERIODS",
        database=connection_settings.database_name,
        schema=connection_settings.raw_schema,
    )

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

    try:
        execute_sql("BEGIN", session=session, conn=conn)

        execute_many(
            f"""
            DELETE FROM {target_table}
            WHERE BENCHMARK_PERIOD_KEY = ?
            """,
            delete_params,
            session=session,
            conn=conn,
        )

        execute_many(
            f"""
            UPDATE {target_table}
            SET
                BENCHMARK_PERIOD_KEY = ?,
                BENCHMARK_PERIOD_NAME = ?,
                PERIOD_START_DATE = ?,
                PERIOD_END_DATE = ?,
                PERIOD_MONTH_COUNT = ?
            WHERE BENCHMARK_PERIOD_KEY = ?
            """,
            update_params,
            session=session,
            conn=conn,
        )

        execute_sql("COMMIT", session=session, conn=conn)

    except Exception:
        execute_sql("ROLLBACK", session=session, conn=conn)
        raise

    return {
        "updated": len(update_params),
        "deleted": len(delete_params),
    }
