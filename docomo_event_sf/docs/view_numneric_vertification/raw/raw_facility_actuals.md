# raw_facility_actuals 数値検証

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 実績データ`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.RAW.RAW_FACILITY_ACTUALS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_facility_actuals`
- スコープ: 全件（2025.04〜2026.03 全12ヶ月分）
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 72,141 |
| BigQuery | 72,141 |
| 一致レコード | 72,141 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型統一のみ: num→float(小数9桁) / date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- `#N/A` 等の Excel エラー（空セル・＠・中止・確認中など）は Python 側で NULL 吸収。「なし」→0 / カンマ除去数値化もアップローダ側で処理済み。
- 除外列 `source_sheet_name`: SF=正規化 yyyymm（`202510`）/ BQ=生シート名（`2025.1`）の設計差のため比較対象外。

## 5. カラム別差分
- `source_sheet_name` を除く全列一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5。`source_sheet_name` 除外後）
- Snowflake: `893617f6b2cf9e368c75542e004f4d7a`
- BigQuery: `893617f6b2cf9e368c75542e004f4d7a`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `source_sheet_name` 表記差 | 72,141 | SF=yyyymm 正規化（例: `202510`）/ BQ=生シート名（例: `2025.1`）。データ本体は同一であり SF 表記が設計仕様。 | 比較対象外（許容） |

- `#N/A` 等の Excel エラーはアップローダ側で NULL に変換済みのため差分にはならない。

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
- 補足: アップローダが横持ち `RAW_FACILITY_ACTUALS_<yyyymm>`（12ヶ月分）を縦持ち化（melt＋クレンジング: 空セル削除 / ＠・中止・確認中→NULL / なし→0 / カンマ除去数値化）して生成した `RAW_FACILITY_ACTUALS` が、BQ の `raw_facility_actuals` と `source_sheet_name` 除外後に完全一致（ハッシュ一致）することを確認した。
