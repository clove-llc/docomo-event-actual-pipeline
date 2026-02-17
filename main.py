import logging

from google.cloud import storage
from google.cloud import bigquery

from src.config.config import get_settings
from src.config.logging_config import setup_logging

from src.application.pipelines.venue_performance_pipeline import (
    VenuePerformancePipeline,
)

from src.infrastructure.repositories.bq_venue_performance_repository import (
    BqVenuePerformanceRepository,
)
from src.infrastructure.repositories.gcs_event_actual_repository import (
    GcsEventActualRepository,
)

from src.domain.transformers.event_actual_transformer import EventActualTransformer


setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("実績データ更新処理を開始します。")

    project_id, event_actual_blob = get_settings()

    gcs_client = storage.Client(project=project_id)
    bq_client = bigquery.Client(project=project_id)

    input_repository = GcsEventActualRepository(client=gcs_client)
    output_repository = BqVenuePerformanceRepository(client=bq_client)

    transformer = EventActualTransformer()

    pipeline = VenuePerformancePipeline(
        input_repository=input_repository,
        transformer=transformer,
        output_repository=output_repository,
    )

    pipeline.run(event_actual_blob)

    logger.info("実績データ更新処理が完了しました。")


if __name__ == "__main__":
    main()
