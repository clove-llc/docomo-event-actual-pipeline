# docomo-event-actual-pipeline

## Snowflakeでの環境構築手順

※ データベース名・スキーマ名は環境に応じて変更する。

---

### 1. データベース・スキーマ・ステージ・ウェアハウスの作成

以下のクエリを実行する。

```sql

CREATE DATABASE USERDB_D_P01_LAK;
CREATE SCHEMA USERDB_D_P01_LAK.USER_SMCB_01;
CREATE STAGE USERDB_D_P01_LAK.USER_SMCB_01.STREAMLIT_STAGE;

CREATE OR REPLACE WAREHOUSE STREAMLIT_WH WITH
  WAREHOUSE_SIZE = '<warehouse_size>'
  AUTO_SUSPEND = <auto_suspend>
  AUTO_RESUME = <auto_resume>
  INITIALLY_SUSPENDED = <initially_suspended>
  COMMENT = '<comment>';

```

---

### 2. 過去実績期間マスタ管理アプリのデプロイ

Snowflakeのサイト上から先ほど作成した `STREAMLIT_STAGE` に移動し、`BENCHMARK_PERIODS_MANAGER` フォルダ配下に、`streamlit/benchmark_periods_manager` フォルダ配下のリソースを全てアップロードする。

その後、以下のコマンドでStreamlitアプリを作成する。

```sql
CREATE OR REPLACE STREAMLIT USERDB_D_P01_LAK.USER_SMCB_01.UPLOADER_XLSX
  ROOT_LOCATION = '@USERDB_D_P01_LAK.USER_SMCB_01.STREAMLIT_STAGE/UPLOADER_XLSX'
  MAIN_FILE = 'app.py'
  QUERY_WAREHOUSE = STREAMLIT_WH;
```

アプリが作成できたら、以下の期間を追加しておく。

1. 2025年4月1日 ~ 2026年3月31日
2. 2025年10月1日 ~ 2026年2月28日
3. 2025年10月1日 ~ 2025年12月31日

---

### 3. ビューの作成

`docomo_event_sf/create_or_replace_view_queries`フォルダ内のSQLを以下の順番で実行する。

1. source_creation配下のSQL（順不同）
2. staging配下のSQL（順不同）
3. intermediate配下のSQL
    - フォルダ・ファイルの番号の小さい順に実行
4. marts配下のSQL（順不同）

---

### 4. マートテーブルの作成

`operations_queries/最終マートテーブル作成用.sql`を実行する。

※ このクエリはRAW層のテーブル内のデータ更新があるたびに実行する必要がある。

---

### 5. 各種Streamlitアプリのデプロイ

#### 5.1 UPLOADER_XLSXのデプロイ

Snowflakeのサイト上から先ほど作成した `STREAMLIT_STAGE` に移動し、`UPLOADER_XLSX` フォルダ配下に、`streamlit/uploader` フォルダ配下のリソースを全てアップロードする。

#### 5.2 EVENT_PLAN_WORKBOOK_BUILDERのデプロイ

Snowflakeのサイト上から先ほど作成した `STREAMLIT_STAGE` に移動し、`EVENT_PLAN_WORKBOOK_BUILDER` フォルダ配下に、`streamlit/event_plan_workbook_builder` フォルダ配下のリソースを全てアップロードする。

---

## 日付実績のクレンジング

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
