# stg_facility_actuals 数値検証（実績データ）

Snowflake 移行後の staging ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 実績データ --layer stg`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.STG.STG_FACILITY_ACTUALS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_facility_actuals`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 72,141 |
| BigQuery（移行元） | 72,141 |
| 一致レコード | 72,141 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: `source_sheet_name`（設計差。詳細は「7. 既知差分」参照）。

## 5. カラム別差分
- `source_sheet_name` を除く**全列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5、source_sheet_name 除外後）
- BigQuery: `800a2c9ef63cadaad5bebba5d7693bec`
- Snowflake: `800a2c9ef63cadaad5bebba5d7693bec`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `source_sheet_name` 表記差 | 全72,141件 | SF=正規化 yyyymm（例: `202510`）/ BQ=生シート名（例: `2025.1`）。SF側の設計どおりの正規化。データ本体は同一。 | 比較対象外（許容） |

## 8. 判定
- 判定: **OK**（`source_sheet_name` は設計差として許容。それ以外の全列は完全一致）
