# docomo_event_sf（Snowflake 移行用 dbt プロジェクト）

BigQuery の `docomo_event` から **Snowflake へ移行**するための dbt プロジェクト。
既存 BQ プロジェクトとは**完全に分離**し、移行が完了したら旧 `docomo_event` を廃止する。

## 前提
- `~/.dbt/profiles.yml` に Snowflake 接続 `dbt_project`（env_var ベース）が定義済み。
- 必要な環境変数: `SNOWFLAKE_ACCOUNT / SNOWFLAKE_USER / SNOWFLAKE_PRIVATE_KEY_PATH / SNOWFLAKE_ROLE / SNOWFLAKE_DATABASE / SNOWFLAKE_WAREHOUSE / SNOWFLAKE_SCHEMA`。
- **`SNOWFLAKE_SCHEMA` は RAW_* の置き場（例: `STREAMLIT_UPLODER_XLSX`）** を指定する。
- RAW_* は `streamlit/uploader` のアップローダが Excel からロードする（このプロジェクトは変換のみ）。

## レイヤとスキーマ
`generate_schema_name` により、`+schema` 指定時は `target.schema_<suffix>` に出力する。
- `staging` → `<schema>_STG`（view）
- `intermediate` → `<schema>_INT`（table）… 例 `STREAMLIT_UPLODER_XLSX_INT`
- `marts` → `<schema>_MART`（table）

## モデル構成（intermediate）
- `実績データ_源泉作成/raw_facility_actuals` … 月別横持ち → 縦持ち（`get_relations_by_pattern` で全月自動）
- `人流・デシルマスタ_源泉作成/s1〜s6` … SENSE → 施設&日付フラグ別 デシルランク（平均値ベース）
- `季節指数マスタ_源泉作成/s1〜s3` … SENSE → 施設別日付フラグ別 季節指数マスタ（偏差値版）

RAW_* は `models/_sources.yml` で source 定義（`{{ source('raw', 'RAW_...') }}`）。

## 実行
```bash
cd docomo_event_sf
dbt deps
dbt run            # 全モデル
dbt run --select "人流・デシルマスタ_源泉作成"   # パイプライン単位
```

## 移行方針
BQ の各モデルを本プロジェクトへ移植 → 値突合（Excel / 旧BQ）→ 一致確認 → 切替 →
最終的に旧 `docomo_event` を廃止し、本プロジェクトに一本化する。
