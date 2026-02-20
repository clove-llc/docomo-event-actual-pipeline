import logging
import pandas as pd
from google.cloud import bigquery

logger = logging.getLogger(__name__)


class BigQueryRepository:
    def __init__(self, client: bigquery.Client, data_set: str):
        self._client = client
        self.data_set = data_set

    def _get_full_table_id(self, table_name: str) -> str:
        return f"{self._client.project}.{self.data_set}.{table_name}"

    def save_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        schema: list[bigquery.SchemaField],
    ) -> None:
        full_table_id = self._get_full_table_id(table_name)

        logger.info("BigQueryへデータロードを開始します: %s", full_table_id)

        # 列順をスキーマ順に整える
        df = df[[field.name for field in schema]]

        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=schema,
            autodetect=False,
        )

        job = self._client.load_table_from_dataframe(
            df,
            full_table_id,
            job_config=job_config,
        )

        job.result()

        logger.info("BigQueryへのデータロード完了: %s", full_table_id)

    def execute_query(self, query: str) -> None:
        logger.info("BigQueryクエリ実行開始")
        job = self._client.query(query)
        job.result()
        logger.info("BigQueryクエリ実行完了")
