import logging


from src.bigquery_repository import (
    BigQueryRepository,
)
from src.google_spreadsheets_repository import GoogleSpreadSheetsRepository
from src.transformer import EventActualTransformer
from src.utils import load_sql


logger = logging.getLogger(__name__)


def run_venue_performance_pipeline(
    input_repository: GoogleSpreadSheetsRepository,
    output_repository: BigQueryRepository,
    sheet_id: str,
) -> None:
    logger.info("実績データ更新処理を開始します。")

    transformer = EventActualTransformer()

    spreadsheets = input_repository.fetch_spreadsheets(sheet_id)

    logger.info("Googleスプレッドシートを解析し、クレンジングを行います。")
    df = transformer.transform(spreadsheets)
    logger.info("クレンジング完了。")

    output_repository.save_venue_performance(df)

    logger.info("実績データ更新処理が完了しました。")


def refresh_derived_tables(
    derived_sql_files: list[str], output_repository: BigQueryRepository
) -> None:
    logger.info("関連テーブルの更新を開始します。")

    for sql_file in derived_sql_files:
        logger.info("%sの更新を行います。", sql_file)
        create_facility_daily_actual_sql = load_sql(sql_file)
        output_repository.execute_query(create_facility_daily_actual_sql)
        logger.info("%sの更新が完了しました。", sql_file)

    logger.info("関連テーブルの更新を開始します。")
