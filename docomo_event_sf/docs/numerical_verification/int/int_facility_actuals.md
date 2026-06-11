# int_facility_actuals 数値検証（実績データ・中間層）

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `export SNOWFLAKE_ACCOUNT="WFJVSLU-VT27190" SNOWFLAKE_USER="DAISUKE_HARATO" SNOWFLAKE_ROLE="ACCOUNTADMIN" SNOWFLAKE_DATABASE="HARATO" SNOWFLAKE_WAREHOUSE="STREAMLIT_WH" SNOWFLAKE_PRIVATE_KEY_PATH="/Users/d.harato/.snowflake/clove_dcc.p8" && .venv/bin/python docomo_event_sf/tools/verify_code.py --table "実績(int)" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_ACTUALS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_actuals`
- スコープ: 全件・全12ヶ月（2025.04〜2026.03）。`source_sheet_name` を除く全列。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 72,087 |
| BigQuery（移行元） | 72,087 |
| 一致レコード | 72,087 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型表現差のみ吸収: num→float(小数9桁) / date→`YYYY-MM-DD` / str はそのまま（trim しない）。
- `#N/A`（area_raw / floor_label / helper_company_name 等）は Python 側で NULL 吸収（BQ=文字列 "#N/A" / SF=NULL）。
- `source_sheet_name` は比較対象外（後述）。

## 5. カラム別差分
- `source_sheet_name` を除く全列一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5。source_sheet_name 除く）
- Snowflake: `94eccc4888fb279faaa06d2121ca331c`
- BigQuery: `94eccc4888fb279faaa06d2121ca331c`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `source_sheet_name` の表記 | 3,041（10月分） | SF=正規化 yyyymm `202510` / BQ=float桁落ち `2025.1`。元Excelシート名「2025.10」をBQはfloat変換で1桁落とし、SFは正規化済み | **比較対象外（exclude）**。SFの `202510` が正（10月）。データ本体（event_date・actual_value 等）は完全一致 |

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
- 補足: `source_sheet_name` を除外した全列でハッシュ完全一致（`94eccc4…`）。int 層の件数（72,087件）は stg 層（72,141件）より54件少ないが、これは int 変換ロジックの集計・結合処理によるものであり、BQ/SF 間で同数が一致していることを確認済み。
