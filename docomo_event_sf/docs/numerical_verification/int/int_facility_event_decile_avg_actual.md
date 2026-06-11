# int_facility_event_decile_avg_actual 数値検証（デシル平均実績・中間層）

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `export SNOWFLAKE_ACCOUNT="WFJVSLU-VT27190" SNOWFLAKE_USER="DAISUKE_HARATO" SNOWFLAKE_ROLE="ACCOUNTADMIN" SNOWFLAKE_DATABASE="HARATO" SNOWFLAKE_WAREHOUSE="STREAMLIT_WH" SNOWFLAKE_PRIVATE_KEY_PATH="/Users/d.harato/.snowflake/clove_dcc.p8" && .venv/bin/python docomo_event_sf/tools/verify_code.py --table "デシル平均実績" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_EVENT_DECILE_AVG_ACTUAL`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_event_decile_avg_actual`
- スコープ: 全件（4,184行）。キー: benchmark_period_key / facility_code / date_flag / decile_rank。集計列: total_actual（SUM）・actual_days（COUNT）・avg_actual（round_bq(avg(actual), 0)）。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 4,184 |
| BigQuery（移行元） | 4,184 |
| 一致レコード | 4,175 |
| Snowflakeのみ | 9 |
| BigQueryのみ | 9 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型表現差のみ吸収: num→float（小数9桁） / date→`YYYY-MM-DD` / str はそのまま（trim しない）。
- `#N/A` は Python 側で NULL 吸収（BQ=文字列 "#N/A" / SF=NULL）。
- 比較から外す列: なし（全列比較）。

## 5. カラム別差分
| 列 | 型 | 不一致行数 | 差分の内容 |
|---|---|--:|---|
| avg_actual | FLOAT | 9 | BQ と SF で常に ±1 の差。total_actual・actual_days・全キー列は完全一致。代表例: facility_code=58（ららぽーと富士見）/ date_flag=通常土日 / decile_rank=1 / period=2025_10_2026_02 → total_actual=407, actual_days=22, BQ=18, SF=19 |

その他全列（benchmark_period_key / benchmark_period_name / period_start_date / period_end_date / facility_code / facility_name / po_level / regional_office / branch_office / date_flag / decile_rank / total_actual / actual_days）は**完全一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `283fc903d4e27645162d63b357b92378`
- BigQuery: `ed831274437a21af789c5310db241097`
- 一致: 不一致（avg_actual の 9 行差に起因。想定どおり）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `avg_actual` の ±1 差 | 9行（全4,184行の0.2%） | FLOAT 演算順序差（要因B・後述） | **許容**（ロジック誤りなし） |

### 要因B: FLOAT 演算順序差（消去不能）

平均を `FLOAT` で集計するため、BQ と SF で合計の最下位ビット（小数16桁目、1〜5 ULP、絶対差最大 1.07e-14・相対差 1e-16）が食い違う。源泉 `stg_facility_daily_deviation_zscore` は 289,810 行が生値で完全一致（差ゼロ）であり、乖離は集計時の足し込み順序のみが原因。

avg_actual はこの FLOAT 平均に `round_bq` マクロ（ROUND_HALF_AWAY_FROM_ZERO）を適用して整数化している。平均の真値がちょうど丸め境界（○.5）に乗る行では、最下位ビット差により「BQ 側は 18.4999…→18 / SF 側は 18.5→19」のように丸め後が ±1 割れる。

- 代表例: facility_code=58 / 通常土日 / decile_rank=1 / 2025_10_2026_02 → total=407, days=22, 407÷22=**18.5（丸め境界）**
- 集計・キー・件数はビット一致でロジックは正しく、差は常に ±1 に限定される（ロジック誤りなら任意の大きさでズレるはず）。
- `round_bq` マクロで丸め方は統一済みだが「丸める前の値」が FLOAT 演算順序に起因して食い違うため消去不能。NUMBER 化すれば解消するが、移行元 BQ が FLOAT 計算のため FLOAT で揃える方針とする。

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK（既知の許容差分=FLOAT演算順序差のみ）**
- 補足: total_actual・actual_days・全キー列はビット完全一致。avg_actual の差 9 行（0.2%）は全て ±1 かつ丸め境界起因であることを確認。ロジック誤りや集計漏れは存在しない。
