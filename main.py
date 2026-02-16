import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)


def main():
    input_file_name = input(
        "input_files内にあるファイル名を入力してください（例: input.xlsx）: "
    )

    input_file_path = "./input_files/" + input_file_name.strip()
    logging.info("読み込み中: %s", input_file_path)

    sheet_name = input("シート名を入力してください: ")

    # Excelファイルを読み込む
    # 対象範囲: B〜BG列、4行目以降
    df = pd.read_excel(input_file_path, sheet_name=sheet_name, header=5, usecols="B:BG")

    key_cols = df.columns[0:13]  # No〜実施日数
    date_cols = df.columns[13:]  # 日付列全部

    df_long = df.melt(
        id_vars=key_cols,
        value_vars=date_cols,
        var_name="日付",  # 元の列名（24日(金) など）が入る
        value_name="日付実績",  # セルの中身（@ など）が入る
    )

    # Excel上で未入力（完全空白）の行を削除
    df_long = df_long.dropna(subset=["日付実績"]).reset_index(drop=True)

    # 日付実績のクレンジング
    df_long["日付実績"] = normalize_daily_result(df_long["日付実績"])

    # イベント情報別にソートする
    df_long = df_long.sort_values(by=list(key_cols)).reset_index(drop=True)

    output_file_name = input("出力ファイル名を入力してください（例: output.xlsx）: ")
    output_path = "./output_files/" + output_file_name

    df_long.to_excel(output_path, index=False)

    print("フォーマット完了:", output_path)


def normalize_daily_result(series: pd.Series) -> pd.Series:
    """
    日付実績の正規化
    - 前後空白除去
    - 記号・ステータスをルールに従って正規化
    - NULL許容の整数型(Int64)に変換
    """
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
