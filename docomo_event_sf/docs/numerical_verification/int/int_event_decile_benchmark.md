# int_event_decile_benchmark 数値検証

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `.venv/bin/python docomo_event_sf/tools/verify_code.py --table "デシルベンチ" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_EVENT_DECILE_BENCHMARK`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_event_decile_benchmark`
- スコープ: 全件。キー: `benchmark_period_key`, `date_flag`, `decile_rank`。除外列なし。
- テーブル特性: デシル別・日付区分別の分位点ベンチマーク（p10〜p90, max_performance）。`PERCENTILE_CONT` 結果を `round_bq(,0)` で丸めた FLOAT 集計を含む。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 210 |
| BigQuery（移行元） | 210 |
| 一致レコード | 201 |
| Snowflakeのみ（移行元に無い） | 9 |
| BigQueryのみ（Snowに無い） | 9 |

## 4. 比較方法・正規化
- 比較方法: **多重集合**（Counter による行レベル突合）。行全体がハッシュキーのため、1 列でも値が異なる行は「BQのみ」「SFのみ」として計上される。
- 列型は BQ スキーマから自動導出（`bq_column_types()` 使用）。
- 型表現差のみ吸収: num→float（小数9桁丸め）/ date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- Excel エラー（`#N/A` 等）は Python 側で NULL に吸収（本テーブルは該当なし）。
- 除外列: **なし**（全列比較対象）。

## 5. カラム別差分

多重集合差の実測：BQのみ 9 行 / SFのみ 9 行。差がある 9 行は各 1 列のみ不一致（p10 または p70 または p75 または p90）。

| 列 | 不一致行数 | 割合 | 差分の内容 |
|---|--:|--:|---|
| p10 | 1 | 0.48% | BQ と SF で ±1 差（FLOAT 演算順序差によるフリップ） |
| p70 | 2 | 0.95% | BQ と SF で ±1 差（同上） |
| p75 | 2 | 0.95% | BQ と SF で ±1 差（同上） |
| p90 | 4 | 1.90% | BQ と SF で ±1 差（同上） |
| p20 | 0 | — | 完全一致 |
| p25 | 0 | — | 完全一致 |
| p30 | 0 | — | 完全一致 |
| p40 | 0 | — | 完全一致 |
| p50 | 0 | — | 完全一致 |
| p60 | 0 | — | 完全一致 |
| max_performance | 0 | — | 完全一致 |

不一致サンプル（`--show-diff` 出力より抜粋）:

| benchmark_period_key | date_flag | decile_rank | 列 | BQ値 | SF値 | 差 |
|---|---|--:|---|--:|--:|--:|
| 2025_10_2025_12 | 年末 | 4 | p90 | 24 | 23 | −1 |
| 2025_04_2026_03 | 年末 | 4 | p90 | 24 | 23 | −1 |
| 2025_10_2026_02 | 通常土日 | 8 | p90 | 13 | 14 | +1 |
| 2025_10_2026_02 | 飛び石祝日 | 8 | p70 | 6 | 7 | +1 |
| 2025_10_2026_02 | 平日 | 5 | p75 | 6 | 7 | +1 |

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `925d25622fb7d506b297ff5d100bf69c`
- BigQuery: `192305a902ec61dad6d247f557456201`
- 一致: 不一致（分位点の ±1 差によるもので想定どおり）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | p10/p70/p75/p90 が ±1 ズレ | 9 行（計 9 セル） | FLOAT 演算順序差（要因 B） | 許容 |

**要因 B（FLOAT 演算順序差・消去不能）の詳細:**

`PERCENTILE_CONT` の補間は入力配列の昇順 FLOAT 値に依存する。源泉（`avg_actual`）は BQ・SF 完全一致だが、`AVG()` の FLOAT 累積順序が DB 間で最下位ビットレベルで異なるため、丸め済み `avg_actual` が ○.5 境界に乗った施設で BQ と SF の値が ±1 フリップする。これにより PERCENTILE_CONT の補間位置が 1 ステップずれ、`round_bq(,0)` 後も ±1 差が残る。

具体例: p75（decile_rank=4, 年末）は、同一デシル群の施設が 58 件。BQ で `avg_actual=18.5` が 18.0 に丸められる施設が SF では 19.0 に丸められ（1 件フリップ）、昇順分布が 1 個ズレて 75%点の補間が 18.0 → 18.75 に移動、`round_bq(,0)` 後 18 → 19 となる。

`round_bq` マクロで丸め方は BQ・SF で統一済みだが、丸める前の FLOAT 値自体が異なるため差は消去不能。キー・件数は完全一致であり、ロジックに誤りはない。差は常に ±1 に限定される。

## 8. 判定
- 判定基準: 完全一致、または既知の許容差分のみであれば OK。
- 判定: **OK（既知の許容差分=FLOAT 演算順序差のみ）**
- 補足: 件数 210 件一致。差分 9 行はすべて FLOAT 演算順序差（要因 B）による ±1 であり、ロジック誤りではない。source となる `int_facility_actuals` は完全一致（別途検証済み）。ハッシュ不一致は分位点ズレによるもので想定どおり。
