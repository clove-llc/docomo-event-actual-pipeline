from abc import ABC, abstractmethod

import pandas as pd
from google.cloud import bigquery

from src.utils import to_boolean, to_date, to_integer, to_string


class BaseTransformer(ABC):
    sheet_name: str
    bq_table_name: str
    bq_schema: list[bigquery.SchemaField]

    def _add_missing_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        for field in self.bq_schema:
            if field.name not in df.columns:
                df[field.name] = None

        return df

    def _align_dataframe_types(self, df: pd.DataFrame) -> pd.DataFrame:
        schema_map = {field.name: field.field_type for field in self.bq_schema}

        for field_name, field_type in schema_map.items():
            if field_name not in df.columns:
                continue

            if field_type == "STRING":
                df[field_name] = to_string(df[field_name])

            elif field_type == "INTEGER":
                df[field_name] = to_integer(df[field_name])

            elif field_type == "BOOLEAN":
                df[field_name] = to_boolean(df[field_name])

            elif field_type == "DATE":
                df[field_name] = to_date(df[field_name])

        return df

    def run(self, raw_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        df = self.transform(raw_data)

        df = self._add_missing_columns(df)
        df = self._align_dataframe_types(df)

        return df

    @abstractmethod
    def transform(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Google Sheetsから取得したデータを整形し、
        BigQueryにロード可能なDataFrameを返す。
        """
        pass
