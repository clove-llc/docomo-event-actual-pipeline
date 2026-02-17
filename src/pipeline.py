import logging

from google.cloud import storage
from google.cloud import bigquery

from src.infrastructure.repositories.bq_venue_performance_repository import (
    BqVenuePerformanceRepository,
)
from src.infrastructure.repositories.gcs_event_actual_repository import (
    GcsEventActualRepository,
)
from src.transformers.event_actual_transformer import EventActualTransformer


logger = logging.getLogger(__name__)


def run_venue_performance_pipeline(project_id, blob_name: str):
    logger.info("Pipeline開始")

    gcs_client = storage.Client(project=project_id)
    bq_client = bigquery.Client(project=project_id)

    input_repository = GcsEventActualRepository(gcs_client)
    output_repository = BqVenuePerformanceRepository(bq_client)
    transformer = EventActualTransformer()

    excel_file = input_repository.fetch_excel_file(blob_name)
    df = transformer.transform(excel_file)
    output_repository.save(df)

    logger.info("Pipeline完了")
