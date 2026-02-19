import logging

import gspread
import google.auth
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

from src.bigquery_repository import BigQueryRepository
from src.config.config import get_settings
from src.config.logging_config import setup_logging

from src.google_spreadsheets_repository import GoogleSpreadSheetsRepository
from src.pipeline import refresh_derived_tables, run_venue_performance_pipeline

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    project_id, event_actual_sheet_id, app_env = get_settings()

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
    bigquery_repository = BigQueryRepository(bq_client)

    run_venue_performance_pipeline(
        input_repository=google_spreadsheets_repository,
        output_repository=bigquery_repository,
        sheet_id=event_actual_sheet_id,
    )

    DERIVED_TABLE_SQL_FILES = [
        # "facility_daily_actual.sql",
        # "facility_event_decile_max_actual.sql",
        # "event_decile_benchmark.sql",
        # "facility_event_planning_snapshot.sql",
        # "facility_special_event_planning_summary.sql",
        # "facility_performance_slots_2026_2027.sql",
    ]

    refresh_derived_tables(DERIVED_TABLE_SQL_FILES, bigquery_repository)


if __name__ == "__main__":
    main()
