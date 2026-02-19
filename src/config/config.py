import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_settings():
    load_dotenv()

    app_env = os.getenv("APP_ENV")
    project_id = os.getenv("PROJECT_ID")
    event_actual_sheet_id = os.getenv("EVENT_ACTUAL_SHEET_ID")

    if not app_env:
        raise ValueError("環境変数 APP_ENV が設定されていません。")

    if not project_id:
        raise ValueError("環境変数 PROJECT_ID が設定されていません。")

    if not event_actual_sheet_id:
        raise ValueError("環境変数 EVENT_ACTUAL_SHEET_ID が設定されていません。")

    return project_id, event_actual_sheet_id, app_env
