# docomo-event-actual-pipeline

## Snowflakeでの環境構築手順

※ データベース名・スキーマ名は環境に応じて変更する。

### 1. スキーマの作成

以下のクエリを実行する。

```sql

CREATE SCHEMA DATABASE_NAME.RAW;
CREATE SCHEMA DATABASE_NAME.STG;
CREATE SCHEMA DATABASE_NAME.INT;
CREATE SCHEMA DATABASE_NAME.MART;

```

### 2. RAWテーブルの作成

Excelアップローダーから、全種類のデータをアップロードしてRAW層のテーブルを作成する。

RAW_BENCHMARK_PERIODSについては、Excelアップローダーの対象ではないので、以下のクエリを実行する。

```sql
-- streamlit/benchmark_periods_manager/snowflake_repository.py > init_table関数内で使用しています。

CREATE TABLE IF NOT EXISTS DATABASE_NAME.RAW.RAW_BENCHMARK_PERIODS (
    BENCHMARK_PERIOD_KEY STRING NOT NULL,
    BENCHMARK_PERIOD_NAME STRING NOT NULL,
    PERIOD_START_DATE DATE NOT NULL,
    PERIOD_END_DATE DATE NOT NULL,
    PERIOD_MONTH_COUNT INT NOT NULL
)
```

上記クエリを実行後、過去実績期間マスタ管理アプリからデータを追加する。

### 3. ビューの作成

`docomo_event_sf/create_or_replace_view_queries`フォルダ内のSQLを以下の順番で実行する。

1. source_creation配下のSQL（順不同）
2. staging配下のSQL（順不同）
3. intermediate配下のSQL
    - フォルダ・ファイルの番号の小さい順に実行
4. marts配下のSQL（順不同）

### 4. マートテーブルの作成

`operations_queries/最終マートテーブル作成用.sql`を実行する。

※ このクエリはRAW層のテーブル内のデータ更新があるたびに実行する必要がある。

### 5. 各種Streamlitアプリのデプロイ

各種Streamlitアプリをデプロイする。

**snowコマンドでデプロイする場合***

```bash
-- strealmit/benchmark_periods_manager・streamlit/event_plan_workbook_builder・streamlit/uploader配下で以下を実行する。
snow streamlit deploy --replace --prune --legacy -c <connection_name> --database <database_name> --schema <schema_name>
```

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
