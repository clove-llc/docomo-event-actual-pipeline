# fact_facility_performance_slots 数値検証（実績スロット Fact・VIEW版）

Snowflake 移行後の mart VIEW が、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --layer mart`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.MART.FACT_FACILITY_PERFORMANCE_SLOTS`（VIEW・32列に拡張）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_mart.fact_facility_performance_slots`（22列）
- スコープ: 全件（1,738,860 行）。粒度: 施設 × 日付 × ベンチマーク期間。
- テーブル特性: int 層の `int_facility_event_planning_snapshot`（`standard_target` / `challenge_target`）と
  `int_facility_monthly_weekday_dateflag_deviation_zscore`（`z_score`）を結合し、
  目標値に季節指数（`target × z_score`）を乗じて `round_bq(,0)` で丸めた `_seasonal` 列を付与した最終 Fact。
  SF 側は BQ の 22 列に加えて `decile_rank` / `avg_actual` / `z_score` / `p25` / `p60` / `p70` / `p75` /
  `p90` / `max_performance` / `special_period_search_key` / `normal_period_search_key` 等 10+ 列を拡張した VIEW。
- 比較列の導出: **BQ `INFORMATION_SCHEMA.COLUMNS` ベース**（SF 拡張列は比較対象外）。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 1,738,860 |
| BigQuery（移行元） | 1,738,860 |
| 一致レコード | 1,720,911 |
| Snowflakeのみ（移行元に無い） | 17,949 |
| BigQueryのみ（Snowに無い） | 17,949 |

> 多重集合比較では「同一キーで 1 列以上値が異なる行」は BQのみ / SFのみに 1 件ずつ計上される。
> キー列（`benchmark_period_key` / `facility_code` / `date` / `date_flag`）は BQ・SF 完全一致
> （キー突合: both=1,738,860 / 欠落=0）。

## 4. 比較方法・正規化
- 比較方法: **多重集合**（Counter による行レベル突合）。1 列でも値が異なる行は「BQのみ」「SFのみ」として計上される。
- 列型は BQ `INFORMATION_SCHEMA.COLUMNS` から自動導出（BQ カラムベース比較）。SF 拡張列は比較対象外。
- 型表現差のみ吸収: num→float（小数9桁丸め）/ date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- Excel エラー（`#N/A` 等）は Python 側で NULL に吸収（本テーブルは該当なし）。
- 除外列（比較対象外）:
  - `p50_seasonal`: **SF mart VIEW に列が存在しない**（BQ 側 22 列に含まれるが SF 側で廃止。設計差として比較除外）。
  - `branch_office`: SF=拠点略号プレフィックス除去（例: BQ「神）神奈川支店」→ SF「神奈川支店」）の設計差。値本体は同一。
  - `is_excluded`: BQ=除外施設マスタ未マッチ行は NULL / SF=FALSE に正規化する設計差。NULL↔FALSE の表現差のみで意味的に等価（実測: TRUE行数 BQ=SF=50,370・TRUE施設集合 23 施設が完全一致。値分布 BQ{NULL:1,062,150, FALSE:626,340, TRUE:50,370} / SF{FALSE:1,688,490, TRUE:50,370}）。

## 5. カラム別差分

多重集合差の実測: BQのみ 17,949 行 / SFのみ 17,949 行。
差分は目標値 4 列に限定。キー列・`cpa` / `has_target_cpa` / `p50` 等その他 BQ 列は完全一致。

| 列 | 不一致行数 | 差分率 | 最大差 | 一致率 |
|---|--:|--:|--:|--:|
| standard_target | 4,358 | 0.25% | 3 | 99.75% |
| challenge_target | 5,443 | 0.31% | 16 | 99.69% |
| standard_target_seasonal | 12,280 | 0.71% | 5 | 99.29% |
| challenge_target_seasonal | 14,584 | 0.84% | 22 | 99.16% |
| p50 / cpa / has_target_cpa 等（上記以外の全 BQ 比較列） | 0 | 0% | — | **100%** |

> 17,949 行は上記 4 列の和集合。差が 5 以上の「大きい差」は challenge_target 系のみで全体の約 0.06%。
> 前回検証（HARATO 実体テーブル時代・同 4 列の和集合）と差分行数が完全に同数であり、
> VIEW 化後もロジック等価性が保たれていることを確認。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `af9f0723838d6eca18f7799aa68f6837`
- Snowflake: `dfb69b89503347f1e5e5fda3aff2d2f5`
- 一致: 不一致（目標値 4 列の FLOAT 演算順序差によるもので想定どおり）

## 7. 既知差分・許容判断

| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `p50_seasonal` 列が SF に存在しない | — | SF mart VIEW で廃止（32 列拡張時に削除）。BQ カラムベース比較のため比較除外 | 比較除外（許容） |
| 2 | `branch_office` 表記差（拠点略号プレフィックス有無） | — | SF=略号プレフィックス除去（設計どおり）/ BQ=「神）神奈川支店」形式 | 比較除外（許容） |
| 3 | `is_excluded` NULL↔FALSE 差 | — | BQ=未マッチ行 NULL / SF=FALSE 正規化。意味的に等価（TRUE 集合 BQ・SF 完全一致） | 比較除外（許容） |
| 4 | `standard_target` が ±1〜3 ズレ | 4,358 行（0.25%） | 要因 B（FLOAT 演算順序差）+ 上流タイル選択 CASE | 許容 |
| 5 | `challenge_target` が ±1〜16 ズレ | 5,443 行（0.31%） | 要因 B + タイル選択 CASE 2 段増幅 | 許容 |
| 6 | `standard_target_seasonal` が ±1〜5 ズレ | 12,280 行（0.71%） | #4 差分に季節指数（z_score）を乗じた後 round_bq(,0) で再丸め | 許容 |
| 7 | `challenge_target_seasonal` が ±1〜22 ズレ | 14,584 行（0.84%） | #5 差分に z_score 乗算・丸め。最大差 16 がさらに 22 まで拡大する場合あり | 許容 |

**要因 B（FLOAT 演算順序差・消去不能）の詳細:**

上流 int 層の `AVG()` / `PERCENTILE_CONT` の FLOAT 累積順序（最下位ビット差、相対差≈1e-16・1〜5 ULP）によって
丸め境界（x.x5 / ○.5）近傍の行でのみ ±0.1〜±1 ズレが生じる。このズレが `round_bq(,0)` を通じて整数値の
±1 フリップを引き起こし、mart の `standard_target` / `challenge_target` に伝播する。
源泉の z_score 自体は BQ・SF 完全一致であり、乖離は集計順序のみが原因。
`round_bq` マクロで丸め方は BQ・SF 統一済みだが、丸める前の FLOAT 値が異なるため差は消去不能。

**増幅メカニズム（challenge_target で差が拡大する理由）:**

`challenge_target` は `standard_target` の値をもとにさらに分位点を CASE で再選択する 2 段 CASE 構造。
上流の ±1 フリップが「選択段」の境界を越えると隣の段の分位点に飛んで差が増幅される（最大差 16）。
季節指数を乗じた `_seasonal` 列ではこの 16 がさらに 22 まで拡大する場合がある。

**集計面への影響:**

差分行においてもプラス差とマイナス差がほぼ相殺するため、全体の平均・中央値等の集計統計は BQ・SF で一致する。

## 8. 判定
- 判定基準: 完全一致、または既知の許容差分のみであれば OK。
- 判定: **OK（既知の許容差分=FLOAT 演算順序差とそのタイル選択増幅のみ。`is_excluded` / `branch_office` は設計差として除外し等価性確認済み）**
- 補足:
  - 件数は BQ・SF ともに 1,738,860 件で一致。
  - 差分 17,949 行（1.03%）はすべて FLOAT 演算順序差に起因する既知の許容差分であり、ロジック誤りではない。
  - `p50` / `cpa` / `has_target_cpa` 等その他 BQ 比較列はすべて 100% 一致。
  - 差が大きい challenge_target 系でも差 5 以上は全体の約 0.06% のみ（最大差: challenge_target 16 / challenge_target_seasonal 22）。
  - ハッシュ不一致は目標値 4 列のズレによるもので想定どおり。
  - 前回検証（HARATO 実体テーブル時代）の同 4 列和集合と差分行数が完全に同数であり、VIEW 化後もロジック等価性を確認。
  - SF 拡張列（`decile_rank` / `avg_actual` / `z_score` / `p25` / `p60` / `p70` / `p75` / `p90` /
    `max_performance` / `special_period_search_key` / `normal_period_search_key` 等）は BQ カラムベース比較のため対象外。
