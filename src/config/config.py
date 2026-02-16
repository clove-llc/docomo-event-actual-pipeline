import logging
import os
from dotenv import load_dotenv

from src.infrastructure.gsc_client import GoogleCloudStorageClient

logger = logging.getLogger(__name__)

def get_settings():
    load_dotenv()

    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    event_actual_file = os.getenv("EVENT_ACTUAL_FILE")

    if not gcp_project_id or not dataset_id or not event_actual_file:
        raise ValueError(
            "環境変数 GCP_PROJECT_ID, BQ_DATASET_ID, EVENT_ACTUAL_FILE が設定されていません。"
        )

    gsc_client = GoogleCloudStorageClient(
        gcp_project_id=gcp_project_id,
        bucket_name="docomo_event_actual",
    )

    return event_actual_file, gsc_client

