# int_facility_actuals 数値検証（実績(int)）

Snowflake 移行後の int ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 実績(int)`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.INT.INT_FACILITY_ACTUALS`（VIEW）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_actuals`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 72,087 |
| BigQuery（移行元） | 72,087 |
| 一致レコード | 72,087 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: `source_sheet_name`（SF=正規化 yyyymm `202510` / BQ=生シート名 `2025.10` の設計差。データ本体は同一）。

## 5. カラム別差分
- **全列一致**（`source_sheet_name` 除く比較対象列）。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `94eccc4888fb279faaa06d2121ca331c`
- Snowflake: `94eccc4888fb279faaa06d2121ca331c`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `source_sheet_name` 表記差 | 全行 | SF=yyyymm 正規化（設計どおり）/ BQ=生シート名 | 比較対象外（許容） |

## 8. 判定
- 判定: **OK**（完全一致）
- 補足: 比較対象列に差分なし。除外列の `source_sheet_name` は設計上の表記差であり、データ本体は同一。
