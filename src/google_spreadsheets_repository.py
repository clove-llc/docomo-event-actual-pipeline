import logging
import gspread
import pandas as pd


logger = logging.getLogger(__name__)


class GoogleSpreadSheetsRepository:
    def __init__(self, client: gspread.Client):
        self._client = client

    def fetch_spreadsheets(self, spreadsheet_id: str) -> dict[str, pd.DataFrame]:
        logger.info("Googleスプレッドシートを取得します: %s", spreadsheet_id)

        spreadsheet = self._client.open_by_key(spreadsheet_id)

        logger.info("取得完了。")

        worksheets = spreadsheet.worksheets()

        sheet_data: dict[str, pd.DataFrame] = {}

        for ws in worksheets:
            data = ws.get_all_values()
            df = pd.DataFrame(data)
            sheet_data[ws.title] = df

        return sheet_data
