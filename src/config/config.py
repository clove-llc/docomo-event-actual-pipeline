import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_settings():
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    event_actual_blob = os.getenv("EVENT_ACTUAL_BLOB")

    if not project_id:
        raise ValueError("環境変数 PROJECT_ID が設定されていません。")

    if not event_actual_blob:
        raise ValueError("環境変数 EVENT_ACTUAL_BLOB が設定されていません。")

    return project_id, event_actual_blob
