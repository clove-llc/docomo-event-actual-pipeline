# stg_facility_foot_traffic_avg_and_decile_by_flag 数値検証（人流平均・デシル）

Snowflake 移行後の staging テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-08
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 人流デシル`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_facility_foot_traffic_avg_and_decile_by_flag`
- スコープ: 全件（20列: facility_code / facility_name ＋ 9フラグの人流平均 ＋ 9フラグのデシル区分）
- 源泉: BQ staging は `SELECT *`（passthrough）。SF も `ref('raw_facility_foot_traffic_avg_and_decile_by_flag')` を passthrough。
  その源泉作成層（SF RAW）は GAS/スプレッドシートのロジックを独自再現したもので、BQ raw と一致済み。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 794 |
| BigQuery（移行元） | 794 |
| 一致レコード | 794 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float小数9桁 / str はそのまま・trim しない）。

## 5. カラム別差分
- **全20列一致**（平均9列・デシル9列とも）。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `bef466c171bf1b811df7190528edc0b3`
- BigQuery: `bef466c171bf1b811df7190528edc0b3`
- 一致: ✓

## 7. 既知差分・許容判断
- なし。

## 8. 判定
- 判定: **OK**（完全一致）
