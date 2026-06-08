# stg_facility_actuals 数値検証（実績データ・縦持ち）

Snowflake 移行後の staging テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-08
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 実績データ --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_FACILITY_ACTUALS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_facility_actuals`
- スコープ: 全件・全12ヶ月（2025.04〜2026.03）。13列のうち `source_sheet_name` を除く12列。
- 源泉: BQ staging は `SELECT * EXCEPT(facility_name), TRIM(facility_name)`。SF も `ref('raw_facility_actuals')` に対し同じ TRIM を適用。
  その源泉作成層（SF RAW.RAW_FACILITY_ACTUALS）は月別横持ちを縦持ち化する独自実装で、BQ raw と一致済み。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 72,141 |
| BigQuery（移行元） | 72,141 |
| 一致レコード | 72,141 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型表現差のみ吸収: num→float(小数9桁) / date→`YYYY-MM-DD` / str はそのまま（trim しない）。
- **`#N/A`（area_raw / floor_label / helper_company_name 等）は Python 側で NULL 吸収**（BQ=文字列 "#N/A" / SF=NULL）。

## 5. カラム別差分
- 比較12列とも一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5。source_sheet_name除く12列）
- Snowflake: `16f2c6a0e329d1003dc712f9e9df9d2e`
- BigQuery: `16f2c6a0e329d1003dc712f9e9df9d2e`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `source_sheet_name` の表記 | 3,041（10月分） | SF=正規化 yyyymm `202510` / BQ=生シート名 `2025.1`（設計差） | **比較対象外（exclude）**。データ本体は一致 |
| 2 | `area_raw` 等の `#N/A` | 約600 | BQ=文字列 "#N/A" / SF=NULL | Python で NULL 吸収（許容） |

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
- 補足: stg層で `TRIM(facility_name)` が効くため raw層ハッシュ（`893617…`）から `16f2c6…` に変化。
  RAW_FACILITY_ACTUALS に前後空白を含む facility_name が24件あり、BQ stg / SF stg とも TRIM 済みで一致。
