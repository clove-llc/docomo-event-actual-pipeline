import logging

from src.infrastructure.repositories.bq_venue_performance_repository import (
    BqVenuePerformanceRepository,
)
from src.infrastructure.repositories.gcs_event_actual_repository import (
    GcsEventActualRepository,
)
from src.domain.transformers.event_actual_transformer import EventActualTransformer


logger = logging.getLogger(__name__)


class VenuePerformancePipeline:

    def __init__(
        self,
        input_repository: GcsEventActualRepository,
        transformer: EventActualTransformer,
        output_repository: BqVenuePerformanceRepository,
    ):
        self.input_repository = input_repository
        self.transformer = transformer
        self.output_repository = output_repository

    def run(self, blob_name: str):
        logger.info("Pipeline開始")

        excel_file = self.input_repository.fetch_excel_file(blob_name)
        df = self.transformer.transform(excel_file)
        self.output_repository.save(df)

        logger.info("Pipeline完了")
