# raw_facility_master 数値検証

## 1. メタ情報
- 実施日: 2026-06-05
- 実施者: numerical-verification skill
- 検証コード: `cd docomo_event_sf && python tools/verify_code.py --table 施設マスタ --show-diff`

## 2. 対象
- 比較元（Snowflake）: `HARATO.RAW.RAW_FACILITY_MASTER`（全39列の raw 取込）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_facility_master`（5列）
- スコープ: BQ に存在する**共通5列**（facility_code / facility_name / po_level / regional_office / branch_office）。
  - ※ SF は raw として全39列を保持。BQ に無い 34 列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 794 |
| BigQuery | 794 |
| 一致レコード | 794 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型統一のみ: num→float(小数9桁) / str はそのまま（trim しない）。
- **`#N/A` は Python 側で NULL に吸収**（BQ=文字列 "#N/A" / SF=NULL）。

## 5. カラム別差分
- 共通5列とも一致（#N/A 吸収後）。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `a7c2c7298c35c4d8d16de66f1696029f`
- BigQuery: `a7c2c7298c35c4d8d16de66f1696029f`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `branch_office` の `#N/A`（9004-9006「施設マスタ該当なし」行） | 3 | BQ=文字列 "#N/A" / SF=NULL（VLOOKUP数式エラー由来。pandas が保持できない） | Python で NULL 吸収（許容）。同行の facility_code/facility_name/po_level/regional_office は値ありで比較し一致 |
| 2 | SF の追加34列（raw 全列保持） | — | BQ raw は5列のみ | 比較対象外 |

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
