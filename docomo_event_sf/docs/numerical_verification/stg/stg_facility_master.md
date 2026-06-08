# stg_facility_master 数値検証（施設マスタ）

Snowflake 移行後の staging テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-08
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 施設マスタ`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_FACILITY_MASTER`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_facility_master`
- スコープ: 全件。主要5列（facility_code / facility_name / po_level / regional_office / branch_office）を比較。
- 源泉: BQ staging は `SELECT * EXCEPT(facility_name), TRIM(facility_name)`。SF は `source('raw','RAW_FACILITY_MASTER')`
  に同じ TRIM を適用（SF RAW は小文字クォート識別子のため `"facility_name"` 明示）。`latest_updated_at` は除外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 794 |
| BigQuery（移行元） | 794 |
| 一致レコード | 794 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float / str はそのまま・trim しない）。
- `facility_name` は BQ stg / SF stg とも `TRIM` 済みの値を比較。

## 5. カラム別差分
- **比較5列とも一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5。比較5列）
- Snowflake: `a7c2c7298c35c4d8d16de66f1696029f`
- BigQuery: `a7c2c7298c35c4d8d16de66f1696029f`
- 一致: ✓

## 7. 既知差分・許容判断
- `latest_updated_at` を除外（SF 固有のロード時刻列）。
- 施設マスタは全39列だが、本検証では論理キー5列を対象（残り列は raw 取込のままで移行差なし）。

## 8. 判定
- 判定: **OK**（完全一致）
