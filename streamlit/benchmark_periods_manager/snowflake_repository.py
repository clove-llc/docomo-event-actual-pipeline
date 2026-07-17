from __future__ import annotations

import datetime

from datetime import date
from typing import Any
from entities import BenchmarkPeriod
from snowflake_client import (
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


def init_table() -> None:
    execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS USERDB_D_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS (
            BENCHMARK_PERIOD_KEY STRING NOT NULL,
            BENCHMARK_PERIOD_NAME STRING NOT NULL,
            PERIOD_START_DATE DATE NOT NULL,
            PERIOD_END_DATE DATE NOT NULL,
            PERIOD_MONTH_COUNT INT NOT NULL
        )
        """,
    )


def fetch_benchmark_periods() -> list[BenchmarkPeriod]:
    """Snowflakeから基準期間マスタを取得する。"""
    rows = fetch_all(
        f"""
        SELECT
            BENCHMARK_PERIOD_KEY,
            BENCHMARK_PERIOD_NAME,
            PERIOD_START_DATE,
            PERIOD_END_DATE,
            PERIOD_MONTH_COUNT
        FROM USERDB_D_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS
        ORDER BY
            PERIOD_START_DATE,
            PERIOD_END_DATE,
            BENCHMARK_PERIOD_KEY
        """,
        [],
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
    benchmark_period: BenchmarkPeriod,
) -> None:
    execute_sql(
        f"""
        INSERT INTO USERDB_D_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS (
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
    )


def apply_benchmark_period_updates_and_deletes(
    update_rows: list[tuple[str, BenchmarkPeriod]],
    delete_keys: list[str],
) -> dict[str, int]:
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
        execute_sql("BEGIN")

        execute_many(
            f"""
            DELETE FROM USERDB_D_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS
            WHERE BENCHMARK_PERIOD_KEY = ?
            """,
            delete_params,
        )

        execute_many(
            f"""
            UPDATE USERDB_D_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS
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

        execute_sql("COMMIT")

    except Exception:
        execute_sql("ROLLBACK")
        raise

    return {
        "updated": len(update_params),
        "deleted": len(delete_params),
    }
