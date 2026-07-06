# raw_facility_master 数値検証

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 施設マスタ`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.RAW.RAW_FACILITY_MASTER`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_facility_master`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

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
- 型統一のみ: num→float(小数9桁) / date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- `#N/A` 等の Excel エラーは Python 側で NULL 吸収（本表では該当なし）。
- 除外列 `branch_office`: SF=拠点略号プレフィックス除去（例: BQ「神）神奈川支店」→ SF「神奈川支店」）の設計差のため比較対象外。

## 5. カラム別差分
- `branch_office` を除く全列一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5。`branch_office` 除外後）
- Snowflake: `29da172aaf819f98b982595373797f9d`
- BigQuery: `29da172aaf819f98b982595373797f9d`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `branch_office` 表記差 | 794 | SF=拠点略号プレフィックス除去（例: `神奈川支店`）/ BQ=プレフィックス付き（例: `神）神奈川支店`）。表記のみの設計差、データ内容は同一。 | 比較対象外（許容） |

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
- 補足: `branch_office` 除外後の全794件・全列でハッシュ完全一致。`branch_office` の差分は表記正規化による設計差であり許容。
