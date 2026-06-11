# int_facility_daily_actual 数値検証

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `.venv/bin/python docomo_event_sf/tools/verify_code.py --table "日別実績" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_DAILY_ACTUAL`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_daily_actual`
- スコープ: 全件。列型は BQ `INFORMATION_SCHEMA.COLUMNS` から自動導出。除外列なし。
- テーブル特性: 施設マスタ × 実績データ × 日付マスタの結合 + DISTINCT による日別実績テーブル。FLOAT 集計を含まないため完全一致が期待値。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 30,472 |
| BigQuery（移行元） | 30,472 |
| 一致レコード | 30,472 |
| Snowflakeのみ（移行元に無い） | 0 |
| BigQueryのみ（Snowに無い） | 0 |

## 4. 比較方法・正規化
- 比較方法: **多重集合**（Counter による行レベル突合）。
- 列型は BQ スキーマから自動導出（`types=None` 指定により `bq_column_types()` を使用）。
- 型表現差のみ吸収: num→float（小数9桁丸め）/ date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- Excel エラー（`#N/A` 等）は Python 側で NULL に吸収（本テーブルは該当なし）。
- 除外列: **なし**（全列比較対象）。

## 5. カラム別差分
全列一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `5dbac4c5ce42dfbeef565f4d04006aa3`
- BigQuery: `5dbac4c5ce42dfbeef565f4d04006aa3`
- 一致: ✓

## 7. 既知差分・許容判断
なし。差分ゼロのため、既知差分・許容判断の対象なし。

## 8. 判定
- 判定基準: 完全一致（件数・全列・ハッシュすべて一致）であれば OK。
- 判定: **OK**
- 補足: 件数 30,472 件・ハッシュ完全一致。FLOAT 集計を含まないテーブルのため期待どおりの完全一致。
