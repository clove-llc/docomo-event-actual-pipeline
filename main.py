import logging

from src.config.config import get_settings
from src.config.logging_config import setup_logging
from src.event_acutual_processor import EventActualProcessor
from src.infrastructure.repositories.gsc_docomo_event_actual_repository import GSCDocomoEventActualRepository

setup_logging()
logger = logging.getLogger(__name__)


def main():
    logger.info("実績データの更新処理を開始します。")

    EVENT_ACTUAL_FILE, gsc_client = get_settings()

    gsc_docomo_event_actual_repository = GSCDocomoEventActualRepository(gsc_client)

    event_actual_processor = EventActualProcessor(
        repository=gsc_docomo_event_actual_repository,
        logger=logger
    )

    final_df = event_actual_processor.run(
        blob_name=EVENT_ACTUAL_FILE,
        output_path="output/event_actual_data.xlsx")

    logger.info("実績データの更新処理が完了しました。")

if __name__ == "__main__":
    main()
