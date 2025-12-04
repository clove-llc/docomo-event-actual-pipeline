import pandas as pd

def main():
    input_file_name = input("input_files内にあるファイル名を入力してください（例: input.xlsx）: ")
    input_file_path = "./input_files/" + input_file_name.strip()

    print("ファイルパス: %s" % input_file_path)

    sheet_name = input("シート名を入力してください: ")

    # Excelファイルを読み込む
    # 対象範囲: B〜BG列、4行目以降
    df = pd.read_excel(
        input_file_path,
        sheet_name=sheet_name,
        header=5,
        usecols="B:BG"
    )

    # 不要な上部行を削除する場合の例
    # rows_to_drop = range(1, 50)
    # df = df.drop(index=rows_to_drop, errors="ignore")

    key_cols = df.columns[0:13]   # No〜実施日数
    date_cols = df.columns[13:]   # 日付列全部

    df_long = df.melt(
        id_vars=key_cols,
        value_vars=date_cols,
        var_name="日付",        # 元の列名（24日(金) など）が入る
        value_name="日付実績"   # セルの中身（@ など）が入る
    )

    # イベント情報別にソートする
    df_long = df_long.sort_values(by=list(key_cols)).reset_index(drop=True)

    output_file_name = input("出力ファイル名を入力してください（例: output.xlsx）: ")
    output_path = "./output_files/" + output_file_name

    df_long.to_excel(output_path, index=False)

    print("フォーマット完了:", output_path)

if __name__ == "__main__":
    main()
