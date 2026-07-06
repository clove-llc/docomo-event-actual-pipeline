# stg_facility_foot_traffic_avg_and_decile_by_flag 数値検証（人流デシル）

Snowflake 移行後の staging ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 人流デシル --layer stg`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.STG.STG_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_facility_foot_traffic_avg_and_decile_by_flag`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 794 |
| BigQuery（移行元） | 794 |
| 一致レコード | 794 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: なし。

## 5. カラム別差分
- **全列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `bef466c171bf1b811df7190528edc0b3`
- Snowflake: `bef466c171bf1b811df7190528edc0b3`
- 一致: ✓

## 7. 既知差分・許容判断
- 除外列なし。データ本体に差分なし。

## 8. 判定
- 判定: **OK**（完全一致）
