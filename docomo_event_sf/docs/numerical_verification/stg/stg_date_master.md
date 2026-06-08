# stg_date_master 数値検証（日付マスタ）

Snowflake 移行後の staging テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-08
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 日付マスタ`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_DATE_MASTER`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_date_master`
- スコープ: 全件（16列）
- 源泉: BQ staging は `SELECT *`（passthrough）。SF は `source('raw','RAW_DATE_MASTER')` を passthrough
  （アップローダ付与の `latest_updated_at` のみ除外して BQ stg とスキーマを揃える）。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 730 |
| BigQuery（移行元） | 730 |
| 一致レコード | 730 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（date→`YYYY-MM-DD` / num→float / bool→bool / str はそのまま）。
- `latest_updated_at`（SF アップローダ付与・BQ に無い列）は比較対象外（stg で除外済み）。

## 5. カラム別差分
- **全16列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `6b358516c1ce0d4523373bef38c4233b`
- BigQuery: `6b358516c1ce0d4523373bef38c4233b`
- 一致: ✓

## 7. 既知差分・許容判断
- `latest_updated_at` を除外（SF 固有のロード時刻列）。データ本体に差分なし。

## 8. 判定
- 判定: **OK**（完全一致）
