# stg_facility_name_mappings 数値検証（施設名マッピング）

Snowflake 移行後の staging テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-08
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 施設名マッピング`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.STG.STG_FACILITY_NAME_MAPPINGS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_staging.stg_facility_name_mappings`
- スコープ: 全件（2列: original_name / mapped_name）
- 源泉: BQ staging は `SELECT *`（passthrough）。SF は `source('raw','RAW_FACILITY_NAME_MAPPINGS')` を passthrough
  （`latest_updated_at` のみ除外）。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 935 |
| BigQuery（移行元） | 935 |
| 一致レコード | 935 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（str はそのまま・trim しない）。

## 5. カラム別差分
- **全2列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `df3e6bf2373aed5b23a2f5ab62c6bad7`
- BigQuery: `df3e6bf2373aed5b23a2f5ab62c6bad7`
- 一致: ✓

## 7. 既知差分・許容判断
- `latest_updated_at` を除外（SF 固有のロード時刻列）。データ本体に差分なし。

## 8. 判定
- 判定: **OK**（完全一致）
