import os
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")

if not GCP_PROJECT_ID or not DATASET_ID:
    raise ValueError("環境変数 GCP_PROJECT_ID, BQ_DATASET_ID が設定されていません。")