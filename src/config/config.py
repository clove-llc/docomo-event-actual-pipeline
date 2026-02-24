import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DIMENSION_TABLE_SQL_FILES = [
    "facility_event_decile_master",
    "facility_monthly_weekday_dateflag_deviation_zscore",
    "facility_monthly_dateflag_deviation_zscore",
]

FACT_TABLE_SQL_FILES = [
    "facility_daily_actual.sql",
    "facility_event_decile_max_actual.sql",
    "event_decile_benchmark.sql",
    "facility_event_planning_snapshot.sql",
    "facility_special_event_planning_summary.sql",
    "facility_performance_slots_2026_2027.sql",
]


def is_enabled(env_var_name: str) -> bool:
    val = os.getenv(env_var_name, "false").lower()

    if val == "true":
        return True

    return False


def get_settings():
    load_dotenv()

    app_env = os.getenv("APP_ENV")
    should_update_all_dimensions = is_enabled("SHOULD_UPDATE_ALL_DIMENSIONS")
    project_id = os.getenv("PROJECT_ID")

    facility_master_sheet_id = os.getenv("FACILITY_MASTER_SHEET_ID")
    event_actual_sheet_id = os.getenv("EVENT_ACTUAL_SHEET_ID")
    date_master_2025_2026_sheet_id = os.getenv("DATE_MASTER_2025_2026_SHEET_ID")
    date_master_2026_2027_sheet_id = os.getenv("DATE_MASTER_2026_2027_SHEET_ID")
    facility_daily_deviation_zscore_sheet_id = os.getenv(
        "FACILITY_DAILY_DEVIATION_ZSCORE_SHEET_ID"
    )
    facility_foot_traffic_sum_and_decile_by_flag_sheet_id = os.getenv(
        "FACILITY_FOOT_TRAFFIC_SUM_AND_DECILE_BY_FLAG_SHEET_ID"
    )

    if not app_env:
        raise ValueError("環境変数 APP_ENV が設定されていません。")

    if not project_id:
        raise ValueError("環境変数 PROJECT_ID が設定されていません。")

    if not facility_master_sheet_id:
        raise ValueError("環境変数 FACILITY_MASTER_SHEET_ID が設定されていません。")

    if not date_master_2025_2026_sheet_id:
        raise ValueError(
            "環境変数 DATE_MASTER_2025_2026_SHEET_ID が設定されていません。"
        )
    if not date_master_2026_2027_sheet_id:
        raise ValueError(
            "環境変数 DATE_MASTER_2026_2027_SHEET_ID が設定されていません。"
        )

    if not facility_daily_deviation_zscore_sheet_id:
        raise ValueError(
            "環境変数 FACILITY_DAILY_DEVIATION_ZSCORE_SHEET_ID が設定されていません。"
        )

    if not facility_foot_traffic_sum_and_decile_by_flag_sheet_id:
        raise ValueError(
            "環境変数 FACILITY_FOOT_TRAFFIC_SUM_AND_DECILE_BY_FLAG_SHEET_ID が設定されていません。"
        )

    if not event_actual_sheet_id:
        raise ValueError("環境変数 EVENT_ACTUAL_SHEET_ID が設定されていません。")

    return (
        app_env,
        should_update_all_dimensions,
        project_id,
        facility_master_sheet_id,
        date_master_2025_2026_sheet_id,
        date_master_2026_2027_sheet_id,
        facility_daily_deviation_zscore_sheet_id,
        facility_foot_traffic_sum_and_decile_by_flag_sheet_id,
        event_actual_sheet_id,
    )
