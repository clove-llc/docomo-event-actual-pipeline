# stg_facility_daily_deviation_zscore 数値検証（季節指数＝施設別日付フラグ別 季節指数マスタ・偏差値版）

## 1. メタ情報
- 実施日: 2026-06-05
- 実施者: numerical-verification skill
- 検証コード: `cd docomo_event_sf && python tools/verify_code.py --table 季節指数 --show-diff`

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_facility_daily_deviation_zscore`
- スコープ: 全件（7列: date / facility_code / facility_name / z_score / month / week_number_monthly / date_flag）

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 289,810 |
| BigQuery | 289,810 |
| 一致レコード | 289,810 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型統一のみ（num→float小数9桁 / date→`YYYY-MM-DD` / str はそのまま）。

## 5. カラム別差分
- **全7列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `67a1e060a4e4ade82082d98f5c298dbe`
- BigQuery: `67a1e060a4e4ade82082d98f5c298dbe`
- 一致: ✓

## 7. 既知差分・許容判断
- なし。

## 8. 判定
- 判定: **OK**
- 補足: SENSE → 平均/標準偏差(標本) → 偏差値 → 季節指数(ROUND(偏差値/50,1), min1) の
  Snowflake 再現が BigQuery 本番 source と完全一致。`week_number_monthly` は月曜始まりの月内週番号を SQL で算出。
