import pandas as pd

from src.utils import normalize_daily_result

class EventActualProcessor:
    def __init__(self, repository, logger):
        self.repository = repository
        self.logger = logger

    def load_excel(self, blob_name):
        self.logger.info("Excelファイルをダウンロードしています: %s", blob_name)
        return self.repository.download_excel_as_dataframe(blob_name=blob_name)

    def transform(self, excel_file) -> pd.DataFrame:
        sheet_names = excel_file.sheet_names
        all_data = []

        for sheet_name in sheet_names:
            self.logger.info("%s シートを処理中です...", sheet_name)

            df = pd.read_excel(
                excel_file,
                sheet_name=sheet_name,
                header=3
            )

            df = df.iloc[:, 1:]
            key_cols = df.columns[:13]
            date_cols = df.columns[13:]

            df_long = df.melt(
                id_vars=key_cols,
                value_vars=date_cols,
                var_name="日付",
                value_name="日付実績",
            )

            df_long["シート名"] = sheet_name
            all_data.append(df_long)

        self.logger.info("全てのシートの処理が完了しました。データを結合しています...")
        final_df = pd.concat(all_data, ignore_index=True)

        self.logger.info("日付実績のクレンジングを行っています...")
        final_df = final_df.dropna(subset=["日付実績"]).reset_index(drop=True)
        final_df["日付実績"] = normalize_daily_result(final_df["日付実績"])

        self.logger.info("日付と施設名でデータをソートしています...")
        final_df = final_df.sort_values(
            by=["日付", "施設名"]
        ).reset_index(drop=True)

        return final_df

    def save_excel(self, df: pd.DataFrame, output_path: str):
        self.logger.info("変換後のデータをExcelファイルに保存しています: %s", output_path)
        df.to_excel(output_path, index=False)
        self.logger.info("Excelファイルの保存が完了しました: %s", output_path)

    def run(self, blob_name: str, output_path: str):
        excel_file = self.load_excel(blob_name)
        final_df = self.transform(excel_file)
        self.save_excel(final_df, output_path)
        return final_df
