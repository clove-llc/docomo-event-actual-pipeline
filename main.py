import pandas as pd
import logging

from src.config.config import get_settings
from src.config.logging_config import setup_logging
from src.infrastructure.repositories.gsc_docomo_event_actual_repository import GSCDocomoEventActualRepository

setup_logging()
logger = logging.getLogger(__name__)


def main():
    EVENT_ACTUAL_FILE, gsc_client = get_settings()

    gsc_docomo_event_actual_repository = GSCDocomoEventActualRepository(gsc_client)

    excel_file = gsc_docomo_event_actual_repository.download_excel_as_dataframe(blob_name=EVENT_ACTUAL_FILE)
    sheet_names = excel_file.sheet_names

    all_data = []

    for sheet_name in sheet_names:
        logger.info(" %s シートを処理中です...", sheet_name)

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
            var_name="日付",  # 元の列名（24日(金) など）が入る
            value_name="日付実績",  # セルの中身（@ など）が入る
        )

        # どのシート由来か分かるように追加（おすすめ）
        df_long["シート名"] = sheet_name

        all_data.append(df_long)

    final_df = pd.concat(all_data, ignore_index=True)

    # Excel上で未入力（完全空白）の行を削除
    final_df = final_df.dropna(subset=["日付実績"]).reset_index(drop=True)

    # 日付実績のクレンジング
    final_df["日付実績"] = normalize_daily_result(final_df["日付実績"])

    # イベント情報別にソートする
    final_df = final_df.sort_values(
        by=["日付", "施設名"]
    ).reset_index(drop=True)


    output_file_name = input("出力ファイル名を入力してください（例: output.xlsx）: ")
    output_path = "./output_files/" + output_file_name

    final_df.to_excel(output_path, index=False)

    logger.info("フォーマット完了: %s", output_path)


def normalize_daily_result(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()

    s = s.replace({"": pd.NA, "nan": pd.NA})

    s = s.replace(
        {
            "＠": pd.NA,
            "@": pd.NA,
            "中止": pd.NA,
            "確認中": pd.NA,
            "なし": 0,
        }
    )

    return pd.to_numeric(s, errors="coerce").astype("Int64")


if __name__ == "__main__":
    main()
