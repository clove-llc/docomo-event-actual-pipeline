import logging

from src.config.config import get_settings
from src.config.logging_config import setup_logging

from src.pipeline import run_venue_performance_pipeline


setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    project_id, event_actual_blob = get_settings()

    logger.info("実績データ更新処理を開始します。")
    run_venue_performance_pipeline(project_id=project_id, blob_name=event_actual_blob)

    logger.info("実績データ更新処理が完了しました。")


if __name__ == "__main__":
    main()
