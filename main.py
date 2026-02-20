import logging

import gspread
import google.auth
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

from src.config.config import get_settings
from src.config.logging_config import setup_logging
from src.schemas.date_master_schema import DATE_MASTER_SCHEMA
from src.schemas.facility_daily_deviation_zscore_schema import (
    FACILITY_DAILY_DEVIATION_ZSCORE_SCHEMA,
)
from src.schemas.facility_foot_traffic_sum_and_decile_by_flag_schema import (
    FACILITY_FOOT_TRAFFIC_SUM_AND_DECILE_BY_FLAG_SCHEMA,
)
from src.schemas.facility_master_schema import FACILITY_MASTER_SCHEMA
from src.schemas.facility_statistics_master_schema import FACILITY_STATISTICS_MASTER_SCHEMA
from src.google_spreadsheets_repository import GoogleSpreadSheetsRepository
from src.bigquery_repository import BigQueryRepository
from src.transformers.master_transformer import MasterTransformer
from src.transformers.event_actual_transformer import EventActualTransformer

from src.pipeline import (
    run_pipeline,
    refresh_derived_tables,
)


setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    (
        app_env,
        project_id,
        facility_master_sheet_id,
        date_master_2025_2026_sheet_id,
        date_master_2026_2027_sheet_id,
        facility_daily_deviation_zscore_sheet_id,
        facility_foot_traffic_sum_and_decile_by_flag_sheet_id,
        event_actual_sheet_id,
    ) = get_settings()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    credentials, _ = google.auth.default(scopes=scopes)

    if app_env == "local":
        credentials = Credentials.from_service_account_file(
            "cloud-run-sa.json",
            scopes=scopes,
        )

    gs_client = gspread.authorize(credentials)
    bq_client = bigquery.Client(project=project_id)

    google_spreadsheets_repository = GoogleSpreadSheetsRepository(gs_client)
    bigquery_repository = BigQueryRepository(bq_client, "docomo_eventActual")

    run_pipeline(
        name="施設マスタ",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=facility_master_sheet_id,
        transformer=MasterTransformer(
            sheet_name="facility_master",
            bq_table_name="facility_master",
            bq_schema=FACILITY_MASTER_SCHEMA,
        ),
    )

    run_pipeline(
        name="施設統計情報マスタ",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=facility_master_sheet_id,
        transformer=MasterTransformer(
            sheet_name="facility_statistics_master",
            bq_table_name="facility_statistics_master",
            bq_schema=FACILITY_STATISTICS_MASTER_SCHEMA,
        ),
    )

    run_pipeline(
        name="日付マスタ（2025-2026）",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=date_master_2025_2026_sheet_id,
        transformer=MasterTransformer(
            sheet_name="date_master_2025_2026",
            bq_table_name="date_master_2025_2026",
            bq_schema=DATE_MASTER_SCHEMA,
        ),
    )

    run_pipeline(
        name="日付マスタ（2026-2027）",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=date_master_2026_2027_sheet_id,
        transformer=MasterTransformer(
            sheet_name="date_master_2026_2027",
            bq_table_name="date_master_2026_2027",
            bq_schema=DATE_MASTER_SCHEMA,
        ),
    )

    run_pipeline(
        name="施設・日付フラグ別の偏差値ベースのZスコアマスタ",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=facility_daily_deviation_zscore_sheet_id,
        transformer=MasterTransformer(
            sheet_name="施設別 × 日付フラグ別_季節指数（偏差値版）_縦持ち",
            bq_table_name="facility_daily_deviation_zscore",
            bq_schema=FACILITY_DAILY_DEVIATION_ZSCORE_SCHEMA,
        ),
    )

    run_pipeline(
        name="施設・日付フラグ別の人流合計とデシルランクマスタ",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=facility_foot_traffic_sum_and_decile_by_flag_sheet_id,
        transformer=MasterTransformer(
            sheet_name="facility_foot_traffic_sum_and_decile_by_flag",
            bq_table_name="facility_foot_traffic_sum_and_decile_by_flag",
            bq_schema=FACILITY_FOOT_TRAFFIC_SUM_AND_DECILE_BY_FLAG_SCHEMA,
        ),
    )

    run_pipeline(
        name="実績データ",
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=event_actual_sheet_id,
        transformer=EventActualTransformer(),
    )

    DERIVED_TABLE_SQL_FILES = [
        "facility_daily_actual.sql",
        "facility_event_decile_max_actual.sql",
        "event_decile_benchmark.sql",
        "facility_event_planning_snapshot.sql",
        "facility_special_event_planning_summary.sql",
        "facility_performance_slots_2026_2027.sql",
    ]

    refresh_derived_tables(DERIVED_TABLE_SQL_FILES, bigquery_repository)


if __name__ == "__main__":
    main()
