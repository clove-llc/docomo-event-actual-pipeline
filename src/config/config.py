import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_settings():
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    event_actual_sheet_id = os.getenv("EVENT_ACTUAL_SHEET_ID")

    k_service = os.getenv(
        "K_SERVICE"
    )  # Cloud Run上でデフォルトで設定されている環境変数

    if not project_id:
        raise ValueError("環境変数 PROJECT_ID が設定されていません。")

    if not event_actual_sheet_id:
        raise ValueError("環境変数 EVENT_ACTUAL_SHEET_ID が設定されていません。")

    return project_id, event_actual_sheet_id, k_service
