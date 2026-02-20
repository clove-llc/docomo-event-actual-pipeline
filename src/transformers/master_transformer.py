import pandas as pd

from google.cloud import bigquery

from src.transformers.base_transformer import BaseTransformer


class MasterTransformer(BaseTransformer):
    def __init__(
        self,
        sheet_name: str,
        bq_table_name: str,
        bq_schema: list[bigquery.SchemaField],
    ):
        self.sheet_name = sheet_name
        self.bq_table_name = bq_table_name
        self.bq_schema = bq_schema

    def transform(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        df = data[self.sheet_name]

        df.columns = df.iloc[1]
        df = df.iloc[2:].reset_index(drop=True)

        return df
