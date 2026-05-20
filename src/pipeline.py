import logging

from src.repositories.bigquery_repository import (
    BigQueryRepository,
)
from src.repositories.google_spreadsheets_repository import GoogleSpreadSheetsRepository
from src.transformers.transformer_base import TransformerBase

logger = logging.getLogger(__name__)


def run_pipeline(
    name: str,
    input_repository: GoogleSpreadSheetsRepository,
    output_repository: BigQueryRepository,
    sheet_id: str,
    transformer: TransformerBase,
) -> None:
    logger.info("%s 更新処理を開始します。", name)

    spreadsheets = input_repository.fetch_spreadsheets(sheet_id)

    logger.info("Googleスプレッドシートを解析し、クレンジングを行います。")
    df = transformer.run(spreadsheets)
    logger.info("クレンジング完了。")

    output_repository.save_table(
        table_name=transformer.bq_table_name,
        df=df,
        schema=transformer.bq_schema,
    )

    logger.info("%s 更新処理が完了しました。", name)
