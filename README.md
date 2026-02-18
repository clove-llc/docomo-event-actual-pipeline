# docomo-event-actual-pipeline

Excel の「横持ちテーブル（1 行に日付が横に並んでいる形式）」を  
「縦持ちテーブル（イベント情報 + 日付 + 日付実績）」に変換するためのスクリプトです。

---

## 1. ディレクトリ構成

リポジトリ直下は以下のような構成を想定しています。

```text
excel-table-transposer/
  ├ .venv/              # 仮想環境（任意）
  ├ input_files/        # 入力用 Excel を置くフォルダ
  ├ output_files/       # 変換結果の Excel が出力されるフォルダ
  ├ .gitignore
  ├ README.md
  ├ requirements.txt
  └ transform_excel.py  # 実行スクリプト
```

---

## 2. 初回セットアップ手順

### 2.1 リポジトリをクローン

```bash
   git clone <このリポジトリのURL>
   cd excel-table-transposer
```

### 2.2 仮想環境の作成（任意だが推奨）

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows の場合: .venv\Scripts\activate
```

### 2.3 ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2.4 フォルダの準備

まだ無い場合は、`input_files` と `output_files` を作成します。

```bash
mkdir input_files output_files
```

---

## 3. 使い方

### 3.1 入力ファイルを配置

変換したい Excel ファイル（例: `input.xlsx`）を
`input_files` フォルダの中に置きます。

```text
input_files/
  └ input.xlsx   ← ここに置く
```

### 3.2 スクリプトを実行

プロジェクトのルートディレクトリ（`transform_excel.py` がある場所）で実行します。

```bash
python transform_excel.py
```

### 3.3 実行時の入力（対話式）

実行すると、以下のようにコマンドラインから順に質問されます。

1.  **入力ファイル名**

    ```text
    input_files内にあるファイル名を入力してください（例: input.xlsx）:
    ```

    → 例: `input.xlsx`

    ※ `input_files/` のパスは自動で付くので、ファイル名だけ入力してください。

2.  **シート名**

    ```text
    シート名を入力してください:
    ```

    → 例: `Sheet1`

3.  **出力ファイル名**

    ```text
    出力ファイル名を入力してください（例: output.xlsx）:
    ```

    → 例: `output.xlsx`

    出力先は `output_files/` 配下になります。

4.  **出力の確認**

    正常に終了すると、`output_files/` に指定したファイル名で出力されます。

    ```text
    output_files/
      └ output.xlsx
    ```

    コマンドラインには次のように表示されます。

    ```text
    フォーマット完了: ./output_files/output.xlsx
    ```

---

## 4. 入力・出力

### 4.1 想定している入力フォーマット

- **ヘッダー行**: Excel 上の 6 行目（Python では `header=5` として指定）
- **使用する列**: B〜BG 列（`usecols="B:BG"`）
- **キー列（イベント情報）**: 先頭から 13 列分（`df.columns[0:13]`）
- **日付列**: 14 列目以降（`df.columns[13:]`）

### 4.2 出力される列

出力ファイルは、

- 元のイベント情報（No, 実施月, …, 実施日数）
- `日付` 列
- `日付実績` 列

という構成になります。

---

## 5. カスタマイズ

### 5.1 ヘッダー行が違う場合

ヘッダー行の位置がファイルによって違う場合は、以下を変更してください。

```python
df = pd.read_excel(
    input_file_path,
    sheet_name=sheet_name,
    header=5,      # ← ここを変更（Excel 上のヘッダー行 - 1）
    usecols="B:BG"
)
```

例）Excel の 4 行目がヘッダーなら `header=3` にする。

### 5.2 使用する列の範囲が違う場合

列範囲が B〜BG 以外の場合は `usecols` を変更します。

```python
usecols="C:AZ"
```

のように指定可能です。

### 5.3 キー列・日付列の範囲が違う場合

イベント情報の列数が変わる場合は、ここを調整してください。

```python
key_cols = df.columns[0:13]   # 0〜12列目
date_cols = df.columns[13:]   # 13列目以降
```

---

## 6. クレンジング処理

### 6.1 日付実績のクレンジング

縦持ち化（melt）後の「日付実績」列に対して、以下のクレンジングを行う。

- Excel上で**完全に未入力（空白セル）**の行は削除する。
- セル値の前後空白を除去（TRIM）。
- 記号・ステータス値を下記のルールに従って正規化する。

| 元の値     | 変換後 | 備考                 |
| ---------- | ------ | -------------------- |
| （空白）   | 行削除 | 完全未入力のため除外 |
| `＠` / `@` | NULL   | 未入力扱い           |
| `中止`     | NULL   | 中止状態を示すNULL   |
| `確認中`   | NULL   | 未入力扱い           |
| `なし`     | `0`    | 実績ゼロとして扱う   |
| 数値       | 数値   | そのまま使用         |

- クレンジング後の「日付実績」列は **NULL許容整数型（Int64）** とする。
- NULL は意味を持つ値として保持し、削除しない。

---

Cloud Run Jobsを作成する

```
gcloud run jobs deploy docomo-event-actual-pipeline-prod \
    --source . \
    --tasks 1 \
    --set-env-vars GCP_PROJECT_ID=[プロジェクトID] \
    --set-env-vars EVENT_ACTUAL_BLOB=[実績ファイル名] \
    --max-retries 3 \
    --region us-central1 \
    --project=[プロジェクトID]
```
