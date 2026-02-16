from io import BytesIO
import logging
import pandas as pd

from src.infrastructure.gsc_client import GoogleCloudStorageClient

logger = logging.getLogger(__name__)


class GSCDocomoEventActualRepository:
    def __init__(self, gsc_client: GoogleCloudStorageClient):
        self.gsc_client = gsc_client

    def download_excel_as_dataframe(self, blob_name: str) -> pd.ExcelFile:
        logger.info("Google Cloud Storage から実績データの Excel ファイルをダウンロードしています...")

        blob = self.gsc_client.bucket.blob(blob_name)
        file_bytes = blob.download_as_bytes()

        logger.info("ダウンロードが完了しました。Excel ファイルを DataFrame に変換しています...")

        return pd.ExcelFile(BytesIO(file_bytes))
