# stg_facility_decile_by_flag 数値検証（人流デシル＝施設&日付フラグ別 デシルランク・平均値ベース）

## 1. メタ情報
- 実施日: 2026-06-05
- 実施者: numerical-verification skill
- 検証コード: `cd docomo_event_sf && python tools/verify_code.py --table 人流デシル --show-diff`

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_FACILITY_DECILE_BY_FLAG`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_facility_foot_traffic_avg_and_decile_by_flag`
- スコープ: 全件（20列: facility_code / facility_name ＋ 9フラグの人流平均 ＋ 9フラグのデシル区分）

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 794 |
| BigQuery | 794 |
| 一致レコード | 794 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型統一のみ（num→float小数9桁 / str はそのまま）。

## 5. カラム別差分
- **全20列一致**（平均9列・デシル9列とも）。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `bef466c171bf1b811df7190528edc0b3`
- BigQuery: `bef466c171bf1b811df7190528edc0b3`
- 一致: ✓

## 7. 既知差分・許容判断
- なし。

## 8. 判定
- 判定: **OK**
- 補足: SENSE → 構成比 → 日別人流(KDDI×比) → フラグ付与 → 平均 → デシルランク(平均値ベース) の
  Snowflake 再現が BigQuery 本番 source と完全一致。
