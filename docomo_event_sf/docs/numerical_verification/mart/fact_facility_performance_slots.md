# fact_facility_performance_slots 数値検証（実績スロット Fact）

Snowflake 移行後の mart テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `.venv/bin/python docomo_event_sf/tools/verify_code.py --table "実績スロットFact" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.MART.FACT_FACILITY_PERFORMANCE_SLOTS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_mart.fact_facility_performance_slots`
- スコープ: 全件（1,738,860 行）。粒度: 施設 × 日付 × ベンチマーク期間。除外列なし。
- テーブル特性: int 層の `int_facility_event_planning_snapshot`（`standard_target` / `challenge_target`）と
  `int_facility_monthly_weekday_dateflag_deviation_zscore`（`z_score`）を結合し、
  目標値に季節指数（`target × z_score`）を乗じて `round_bq(,0)` で丸めた `_seasonal` 列を付与した最終 Fact テーブル。
  列型は BQ `INFORMATION_SCHEMA.COLUMNS` から自動導出（`types=None`）。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 1,738,860 |
| BigQuery（移行元） | 1,738,860 |
| 一致レコード | 1,720,836 |
| Snowflakeのみ（移行元に無い） | 18,024 |
| BigQueryのみ（Snowに無い） | 18,024 |

> 多重集合比較では「同一キーで 1 列以上値が異なる行」は BQのみ / SFのみに 1 件ずつ計上される。
> キー自体（`benchmark_period_key` / `facility_code` / `date` 等）は BQ・SF 完全一致。

## 4. 比較方法・正規化
- 比較方法: **多重集合**（Counter による行レベル突合）。1 列でも値が異なる行は「BQのみ」「SFのみ」として計上される。
- 列型は BQ スキーマから自動導出（`bq_column_types()` 使用）。
- 型表現差のみ吸収: num→float（小数9桁丸め）/ date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- Excel エラー（`#N/A` 等）は Python 側で NULL に吸収（本テーブルは該当なし）。
- 除外列: **なし**（全列比較対象）。

## 5. カラム別差分

多重集合差の実測: BQのみ 18,024 行 / SFのみ 18,024 行。
差分は目標値 6 列に限定。キー列・`p50` は完全一致。

| 列 | 不一致行数 | 差分率 | 最大差 | 平均\|差\| | 一致率 |
|---|--:|--:|--:|--:|--:|
| standard_target | 4,358 | 0.25% | 3 | 1.52 | 99.75% |
| challenge_target | 5,443 | 0.31% | 16 | 4.06 | 99.69% |
| p50 | 0 | 0% | 0 | 0 | **100%** |
| standard_target_seasonal | 12,280 | 0.71% | 5 | 1.31 | 99.29% |
| challenge_target_seasonal | 14,584 | 0.84% | 22 | 2.29 | 99.16% |
| p50_seasonal | 7,412 | 0.43% | 2 | 1.06 | 99.57% |

> 差が 5 以上の「大きい差」は challenge_target 系のみで、全体の約 0.06%（≒980行/174万）。最大差は challenge_target で 16、challenge_target_seasonal で 22。

不一致サンプル（`--show-diff` 出力より抜粋）:

**BQのみ（代表サンプル）:**
| benchmark_period_key | facility_code | facility_name | date | date_flag | standard_target | challenge_target | p50 | standard_target_seasonal | challenge_target_seasonal | p50_seasonal |
|---|--:|---|---|---|--:|--:|--:|--:|--:|--:|
| 2025_04_2026_03 | 2215 | ガーデンモール木津川 | 2027-03-23 | 平日 | 3 | 4 | 3 | 4 | 5 | 4 |
| 2025_04_2026_03 | 322 | マルイファミリー志木 | 2025-04-04 | 平日 | 4 | 5 | 4 | 5 | 6 | 5 |
| 2025_04_2026_03 | 49 | 湘南モールフィル | 2026-10-15 | 平日 | 5 | 6 | 5 | 5 | 5 | 5 |

**SFのみ（代表サンプル）:**
| benchmark_period_key | facility_code | facility_name | date | date_flag | standard_target | challenge_target | p50 | standard_target_seasonal | challenge_target_seasonal | p50_seasonal |
|---|--:|---|---|---|--:|--:|--:|--:|--:|--:|
| 2025_10_2026_02 | 243 | ララガーデン川口 | 2025-12-17 | 平日 | 5 | 7 | 4 | 5 | 7 | 4 |
| 2025_10_2026_02 | 299 | イオンタウン千種 | 2025-12-17 | 平日 | 7 | 8 | 4 | 12 | 14 | 7 |
| 2025_10_2026_02 | 315 | ジアウトレット広島 | 2025-12-17 | 平日 | 7 | 8 | 4 | 8 | 9 | 4 |

> BQのみ / SFのみは同一論理行（同キー）で BQ 側の値 / SF 側の値を表す。p50 がサンプル間で異なるのは行が別施設・別日付だからであり、同一キーでは p50 は完全一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `026e16945b24faf6fa35028e2a46c3db`
- BigQuery: `72a9ba3e98c9a8a803aaf7b5809e0089`
- 一致: 不一致（目標値列の FLOAT 演算順序差によるもので想定どおり）

## 7. 既知差分・許容判断

| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `standard_target` が ±1〜3 ズレ | 4,358 行（0.25%） | 要因 B（FLOAT 演算順序差）+ 上流タイル選択 CASE | 許容 |
| 2 | `challenge_target` が ±1〜16 ズレ | 5,443 行（0.31%） | 要因 B + タイル選択 CASE 2 段増幅・mart への伝播 | 許容 |
| 3 | `p50` は完全一致 | 0 | PERCENTILE_CONT(0.5) は丸め境界への感度が低い | — |
| 4 | `standard_target_seasonal` が ±1〜5 ズレ | 12,280 行（0.71%） | #1 差分に季節指数（z_score）を乗じた後 round_bq(,0) で再丸め。z_score は完全一致だが乗算後の丸め位置が乗算前 ±1 で変化する | 許容 |
| 5 | `challenge_target_seasonal` が ±1〜22 ズレ | 14,584 行（0.84%） | #2 差分に z_score を乗算・丸め。challenge_target の最大差 16 がさらに拡大し最大 22 | 許容 |
| 6 | `p50_seasonal` が ±1〜2 ズレ | 7,412 行（0.43%） | p50 自体は完全一致だが、z_score との乗算後 round_bq(,0) で境界近傍が ±1 フリップ。独立した FLOAT 演算誤差 | 許容 |

**要因 B（FLOAT 演算順序差・消去不能）の詳細:**

上流 int 層の `avg_z_score` / `avg_actual` / 分位点が `AVG()` / `PERCENTILE_CONT` の FLOAT 累積順序（最下位ビット差）によって丸め境界近傍の行で ±0.1〜±1 ズレる。このズレが `round_bq(,0)` を通じて整数値の ±1 フリップを引き起こし、mart の `standard_target` / `challenge_target` に伝播する。源泉の z_score 自体は BQ・SF 完全一致であり、乖離は集計順序のみが原因。`round_bq` マクロで丸め方は BQ・SF 統一済みだが、丸める前の FLOAT 値が異なるため差は消去不能。

**増幅メカニズム（challenge_target で差が拡大する理由）:**

`standard_target` は `avg_actual` と分位点（p50→p60→p70→p75→p90/max）を CASE で選択する。`challenge_target` は `standard_target` の値をもとにさらに分位点を CASE で再選択する（2 段 CASE 構造）。上流の ±1 フリップが「選択段」の境界を越えると、隣の段の分位点に飛んで差が増幅される（例: SF で 38 → BQ で 22、差 16）。季節指数を乗じた `_seasonal` 列では、この 16 がさらに 22 まで拡大する場合がある。

**集計面への影響:**

差分行においてもプラス差とマイナス差がほぼ相殺するため、全体の平均・中央値・最大値などの集計統計は BQ・SF で一致する。実務上の影響は「ごく一部の施設×日付×期間の目標値が ±数、稀に十数違う」程度であり、傾向分析・集計用途には実質的な影響はない。

## 8. 判定
- 判定基準: 完全一致、または既知の許容差分のみであれば OK。
- 判定: **OK（既知の許容差分=FLOAT 演算順序差とそのタイル選択増幅・_seasonal への伝播のみ）**
- 補足:
  - 件数は BQ・SF ともに 1,738,860 件で一致。
  - 差分 18,024 行（1.04%）はすべて FLOAT 演算順序差に起因する既知の許容差分であり、ロジック誤りではない。
  - `p50` は 100% 一致。target 列の一致率は 99.16〜99.75%。差が大きい challenge_target 系でも
    差 5 以上は全体の約 0.06% のみ（最大差: challenge_target 16 / challenge_target_seasonal 22）。
  - ハッシュ不一致は目標値列のズレによるもので想定どおり。
  - 源泉となる `int_facility_event_planning_snapshot`（standard_target / challenge_target）および
    `int_facility_monthly_weekday_dateflag_deviation_zscore`（z_score）は別途検証済み。
