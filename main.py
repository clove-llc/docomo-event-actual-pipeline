import logging

from google.cloud import storage
from google.cloud import bigquery

from src.bigquery_repository import BigQueryRepository
from src.cloud_storage_repository import CloudStorageRepository
from src.config.config import get_settings
from src.config.logging_config import setup_logging

from src.pipeline import refresh_derived_tables, run_venue_performance_pipeline

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    project_id, event_actual_blob = get_settings()

    gcs_client = storage.Client(project=project_id)
    bq_client = bigquery.Client(project=project_id)

    cloud_storage_repository = CloudStorageRepository(gcs_client)
    bigquery_repository = BigQueryRepository(bq_client)

    run_venue_performance_pipeline(
        input_repository=cloud_storage_repository,
        output_repository=bigquery_repository,
        blob_name=event_actual_blob,
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
