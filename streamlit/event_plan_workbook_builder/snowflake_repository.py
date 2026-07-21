from __future__ import annotations
import datetime

from datetime import date
from typing import Any
from entities import (
    DateDetail,
    FacilityDailyTargetDetail,
    FacilityDetail,
    RegionalOfficeScheduleConstraint,
)
from snowflake_client import (
    fetch_all,
)

# ====================
# データ型の変換
# ====================


def _to_int_or_none(value) -> int | None:
    return None if value is None else int(value)


def _to_str_or_none(value) -> str | None:
    return None if value is None else str(value)


def _to_date(value: Any) -> date:
    if isinstance(value, datetime.datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


# ====================
# Snowflake からのデータ取得
# ====================


def fetch_benchmark_period_keys() -> list[str]:
    """Snowflakeから過去実績対象期間の一覧を取得する。"""
    rows = fetch_all(
        f"""
            SELECT DISTINCT
                BENCHMARK_PERIOD_KEY
            FROM USERDB_B_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS
            ORDER BY BENCHMARK_PERIOD_KEY DESC
            """,
        [],
    )

    return [str(row[0]) for row in rows]


def fetch_regional_office_schedule_constraints() -> (
    list[RegionalOfficeScheduleConstraint]
):
    """Snowflakeから支社別スケジュール制限マスタの情報を取得する。"""
    rows = fetch_all(
        f"""
        SELECT
            REGIONAL_OFFICE,
            DAILY_EVENT_LIMIT,
            OPERATING_DAYS
        FROM USERDB_B_P01_LAK.USER_SMCB_01.STG_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER
        """,
        [],
    )

    return [
        RegionalOfficeScheduleConstraint(
            regional_office=str(row[0]),
            daily_event_limit=int(row[1]),
            operating_days=str(row[2]),
        )
        for row in rows
    ]


def fetch_facility_daily_target_details(
    benchmark_period_key: str,
    year: int,
    month: int,
    regional_office_name: str,
) -> list[FacilityDailyTargetDetail]:
    """Snowflakeから過去実績対象期間の実績をもとに算出された対象支社の目標値を取得する。"""
    rows = fetch_all(
        f"""
        SELECT
            FACILITY_CODE,
            FACILITY_NAME,
            PO_LEVEL,
            REGIONAL_OFFICE,
            BRANCH_OFFICE,
            DATE,
            DATE_FLAG,
            CPA,
            STANDARD_TARGET_SEASONAL
        FROM USERDB_B_P01_LAK.USER_SMCB_01.FACT_FACILITY_PERFORMANCE_SLOTS_TABLE
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
            branch_office=_to_str_or_none(row[4]),
            date=_to_date(row[5]),
            date_flag=str(row[6]),
            cpa=_to_int_or_none(row[7]),
            target_value=int(row[8]),
        )
        for row in rows
    ]


def fetch_facility_details(
    benchmark_period_key: str,
    year: int,
    month: int,
    regional_office_name: str,
) -> list[FacilityDetail]:
    """Snowflakeから指定された支社の施設詳細情報を取得する。"""
    rows = fetch_all(
        f"""
        SELECT
            F_F_P_S.FACILITY_CODE,
            F_F_P_S.FACILITY_NAME,
            F_F_P_S.PO_LEVEL,
            F_F_P_S.REGIONAL_OFFICE,
            F_F_P_S.BRANCH_OFFICE,
            F_F_P_S.CPA,
            F_S_C_M.MONTHLY_EVENT_LIMIT,
            F_S_C_M.OPERATING_DAYS,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = '平日' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_weekday_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = '通常土日' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_regular_weekend_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = '三連休' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_three_day_holiday_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = '飛び石祝日' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_bridge_holiday_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = 'GW' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_gw_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = 'お盆' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_obon_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = '正月' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_new_year_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = '年末' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_year_end_standard_target_seasonal,
            ROUND(AVG(CASE WHEN F_F_P_S.DATE_FLAG = 'ブラックフライデー' THEN F_F_P_S.STANDARD_TARGET_SEASONAL END)) AS avg_black_friday_standard_target_seasonal
        FROM
            USERDB_B_P01_LAK.USER_SMCB_01.FACT_FACILITY_PERFORMANCE_SLOTS_TABLE AS F_F_P_S
            LEFT JOIN USERDB_B_P01_LAK.USER_SMCB_01.STG_FACILITY_SCHEDULE_CONSTRAINTS_MASTER AS F_S_C_M ON F_F_P_S.FACILITY_CODE = F_S_C_M.FACILITY_CODE
        WHERE F_F_P_S.BENCHMARK_PERIOD_KEY = ?
            AND EXTRACT(YEAR FROM F_F_P_S.DATE) = ?
            AND EXTRACT(MONTH FROM F_F_P_S.DATE) = ?
            AND F_F_P_S.REGIONAL_OFFICE = ?
            AND F_F_P_S.HAS_TARGET_CPA = TRUE
        GROUP BY
            F_F_P_S.FACILITY_CODE,
            F_F_P_S.FACILITY_NAME,
            F_F_P_S.PO_LEVEL,
            F_F_P_S.REGIONAL_OFFICE,
            F_F_P_S.BRANCH_OFFICE,
            F_F_P_S.CPA,
            F_S_C_M.MONTHLY_EVENT_LIMIT,
            F_S_C_M.OPERATING_DAYS
        """,
        [
            benchmark_period_key,
            year,
            month,
            regional_office_name,
        ],
    )

    return [
        FacilityDetail(
            facility_code=int(row[0]),
            facility_name=str(row[1]),
            po_level=str(row[2]),
            regional_office=str(row[3]),
            branch_office=_to_str_or_none(row[4]),
            cpa=_to_int_or_none(row[5]),
            monthly_event_limit=_to_str_or_none(row[6]),
            operating_days=_to_str_or_none(row[7]),
            avg_weekday_standard_target_seasonal=_to_int_or_none(row[8]),
            avg_regular_weekend_standard_target_seasonal=_to_int_or_none(row[9]),
            avg_three_day_holiday_standard_target_seasonal=_to_int_or_none(row[10]),
            avg_bridge_holiday_standard_target_seasonal=_to_int_or_none(row[11]),
            avg_gw_standard_target_seasonal=_to_int_or_none(row[12]),
            avg_obon_standard_target_seasonal=_to_int_or_none(row[13]),
            avg_new_year_standard_target_seasonal=_to_int_or_none(row[14]),
            avg_year_end_standard_target_seasonal=_to_int_or_none(row[15]),
            avg_black_friday_standard_target_seasonal=_to_int_or_none(row[16]),
        )
        for row in rows
    ]


def fetch_date_master(year: int, month: int) -> list[DateDetail]:
    """Snowflakeから指定された年月の日付マスタ情報を取得する。"""
    rows = fetch_all(
        f"""
        SELECT
            DATE,
            WEEKDAY_NAME_AND_WEEK_NUMBER_MONTHLY,
            DATE_FLAG
        FROM USERDB_B_P01_LAK.USER_SMCB_01.STG_DATE_MASTER
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
            date=_to_date(row[0]),
            weekday_name_and_week_number_monthly=str(row[1]),
            date_flag=str(row[2]),
        )
        for row in rows
    ]
