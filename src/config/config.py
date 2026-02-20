import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_settings():
    load_dotenv()

    app_env = os.getenv("APP_ENV")
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
        project_id,
        facility_master_sheet_id,
        date_master_2025_2026_sheet_id,
        date_master_2026_2027_sheet_id,
        facility_daily_deviation_zscore_sheet_id,
        facility_foot_traffic_sum_and_decile_by_flag_sheet_id,
        event_actual_sheet_id,
    )
