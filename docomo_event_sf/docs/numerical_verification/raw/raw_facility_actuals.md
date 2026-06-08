# raw_facility_actuals 数値検証（実績データ・縦持ち／源泉作成）

源泉作成層（GAS/スプレッドシートのロジックを Snowflake で独自再現したテーブル）が、移行元 BigQuery の raw と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-08
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --layer raw --table 実績データ --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.RAW.RAW_FACILITY_ACTUALS`（全12ヶ月 RAW_FACILITY_ACTUALS_<yyyymm> を縦持ち統合。`models/source_creation/raw_facility_actuals.sql`）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_facility_actuals`
- スコープ: 全件・全12ヶ月（2025.04〜2026.03）。13列のうち `source_sheet_name` を除く12列。
- 位置づけ: BQ では raw は外部ロード（GAS等）で dbt SQL を持たない。SF はそのロジックを独自実装で再現し、本検証で BQ raw と一致を担保する。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 72,141 |
| BigQuery（移行元） | 72,141 |
| 一致レコード | 72,141 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型表現差のみ吸収: num→float(小数9桁) / date→`YYYY-MM-DD` / str はそのまま（**trim しない**＝raw層なので原文保持）。
- **`#N/A`（area_raw 等）は Python 側で NULL 吸収**（BQ=文字列 "#N/A" / SF=NULL）。

## 5. カラム別差分
- 比較12列とも一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5。source_sheet_name除く12列）
- Snowflake: `893617f6b2cf9e368c75542e004f4d7a`
- BigQuery: `893617f6b2cf9e368c75542e004f4d7a`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `source_sheet_name` の表記 | 3,041（10月分） | SF=正規化 yyyymm `202510` / BQ=生シート名 `2025.1`（設計差） | **比較対象外（exclude）** |
| 2 | `area_raw` 等の `#N/A` | 約600 | BQ=文字列 "#N/A" / SF=NULL | Python で NULL 吸収（許容） |

## 8. 判定
- 判定: **OK**
- 補足: raw層では facility_name を TRIM しない（前後空白を含む24件も原文保持）。BQ raw も同じく原文保持のため一致。
  （TRIM は stg 層で適用 → [stg/stg_facility_actuals.md] 参照）
