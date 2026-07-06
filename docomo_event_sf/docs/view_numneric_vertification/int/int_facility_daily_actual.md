# int_facility_daily_actual 数値検証（日別実績）

Snowflake 移行後の int ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 日別実績`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.INT.INT_FACILITY_DAILY_ACTUAL`（VIEW）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_daily_actual`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 30,472 |
| BigQuery（移行元） | 30,472 |
| 一致レコード | 30,472 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: `branch_office`（SF=拠点略号プレフィックス除去後の支店名 / BQ=プレフィックス付き表記「神）神奈川支店」。表記のみの設計差。データ本体は同一）。

## 5. カラム別差分
- **全列一致**（`branch_office` 除く比較対象列）。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `90db3ea988a4283f4b9cb15c6c26b98b`
- Snowflake: `90db3ea988a4283f4b9cb15c6c26b98b`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `branch_office` 表記差 | 全行 | SF=拠点略号プレフィックス除去（設計どおり）/ BQ=プレフィックス付き | 比較対象外（許容） |

## 8. 判定
- 判定: **OK**（完全一致）
- 補足: 比較対象列に差分なし。除外列の `branch_office` は表記のみの設計差。
