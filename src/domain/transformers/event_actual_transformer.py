import pandas as pd


class EventActualTransformer:
    HEADER_ROW = 3
    KEY_COLUMN_COUNT = 13

    NORMALIZE_REPLACEMENTS = {
        "": pd.NA,
        "nan": pd.NA,
        "＠": pd.NA,
        "@": pd.NA,
        "中止": pd.NA,
        "確認中": pd.NA,
        "なし": 0,
    }

    COLUMN_MAPPING = {
        "No": "no",
        "実施月": "event_month",
        "支社名": "regional_office_name",
        "支店": "branch_name",
        "施設名": "facility_name",
        "フロア": "floor_label",
        "スペース名": "space_name",
        "面積": "area_raw",
        "ヘルパー会社": "helper_company_name",
        "スタッフ数": "staff_count",
        "開始日": "start_date",
        "終了日": "end_date",
        "実施日数": "actual_days_raw",
        "日付": "date",
        "日付実績": "daily_result_raw",
    }

    def _normalize_daily_result(self, series: pd.Series) -> pd.Series:
        s = series.astype(str).str.strip()
        s = s.replace(self.NORMALIZE_REPLACEMENTS)
        return pd.to_numeric(s, errors="coerce").astype("Int64")

    def _transform_sheet(
        self, excel_file: pd.ExcelFile, sheet_name: str
    ) -> pd.DataFrame:

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            header=self.HEADER_ROW,
        )

        df = df.iloc[:, 1:]

        key_cols = df.columns[: self.KEY_COLUMN_COUNT]
        date_cols = df.columns[self.KEY_COLUMN_COUNT :]

        df_long = df.melt(
            id_vars=key_cols,
            value_vars=date_cols,
            var_name="日付",
            value_name="日付実績",
        )

        df_long["datasource"] = sheet_name

        return df_long

    def transform(self, excel_file: pd.ExcelFile) -> pd.DataFrame:
        all_sheet_data: list[pd.DataFrame] = []

        for sheet_name in excel_file.sheet_names:
            transformed = self._transform_sheet(excel_file, str(sheet_name))
            all_sheet_data.append(transformed)

        df = pd.concat(all_sheet_data, ignore_index=True)
        df = df.rename(columns=self.COLUMN_MAPPING)

        return (
            df.dropna(subset=["daily_result_raw"])
            .assign(
                daily_result_raw=self._normalize_daily_result(df["daily_result_raw"])
            )
            .sort_values(by=["date", "facility_name"])
            .reset_index(drop=True)
        )
