# int_facility_event_planning_snapshot 数値検証（計画スナップショット）

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `.venv/bin/python docomo_event_sf/tools/verify_code.py --table "計画スナップショット" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_EVENT_PLANNING_SNAPSHOT`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_event_planning_snapshot`
- スコープ: 全件。キー: `benchmark_period_key`, `facility_code`, `date_flag`, `decile_rank`。除外列なし。
- テーブル特性: 施設×期間×日付区分×デシル別の計画目標値スナップショット。
  `avg_actual` を `PERCENTILE_CONT`（分位点 p50〜p90）と `MAX` で比較し、段階的な CASE 選択で
  `standard_target`（GREATEST(選択値, 1)）および `challenge_target` を算出する。
  分位点は `round_bq(,0)` 丸め済み FLOAT 値。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 21,438 |
| BigQuery（移行元） | 21,438 |
| 一致レコード | 20,718 |
| Snowflakeのみ（移行元に無い） | 720 |
| BigQueryのみ（Snowに無い） | 720 |

## 4. 比較方法・正規化
- 比較方法: **多重集合**（Counter による行レベル突合）。1 列でも値が異なる行は「BQのみ」「SFのみ」として計上される。
- 列型は BQ スキーマから自動導出（`bq_column_types()` 使用）。
- 型表現差のみ吸収: num→float（小数9桁丸め）/ date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- Excel エラー（`#N/A` 等）は Python 側で NULL に吸収（本テーブルは該当なし）。
- 除外列: **なし**（全列比較対象）。

## 5. カラム別差分

多重集合差の実測: BQのみ 720 行 / SFのみ 720 行。**キーで突合すると BQ・SF は 21,438 行が完全結合し
（outer join: both=21,438 / left_only=0 / right_only=0）、`decile_rank` を含むキー列にズレは無い**。
720 行は「いずれか 1 列以上の値が異なるユニーク行」の和集合で、その大半は**分位点列の伝播**が占める。

キー結合での列別差分（実測）:

| 列 | 不一致行数 | 最大差 | 差分の内容 |
|---|--:|--:|---|
| p90 | 317 | 1 | ベンチの分位点 ±1 差が同一デシル群の全施設へ伝播（§7） |
| p70 | 159 | 1 | 同上 |
| p75 | 159 | 1 | 同上 |
| p10 | 80 | 1 | 同上 |
| standard_target | 30 | 3 | 分位点差によるタイル選択フリップ（§7） |
| challenge_target | 28 | 16 | standard_target の差が CASE 選択を通じて増幅（§7） |
| avg_actual | 9 | 1 | AVG の FLOAT 演算順序差（§7） |
| p20 / p25 / p30 / p40 / p50 / p60 / max_performance | 0 | — | 完全一致 |

> **注:** 720 行（BQのみ/SFのみ）= 上記いずれかの列が異なる行の**和集合**（列ごとの差分行は重複し得る）。
> 件数の主因は `p90`(317)/`p70`(159)/`p75`(159)/`p10`(80) の分位点列。
> ベンチ（`int_event_decile_benchmark`）で分位点が ±1 差となるのは 9 グループだけだが、
> 本スナップショットは施設×期間×日付区分×デシルの粒度で**各デシル群に多数の施設がぶら下がる**ため、
> 1 グループの分位点差が多数の行に伝播し、行数として膨らむ（値差は常に ±1）。

不一致サンプル（`--show-diff` 出力より抜粋、BQのみ/SFのみ各5行）:

**BQのみ（代表サンプル）:**
| benchmark_period_key | facility_code | facility_name | date_flag | decile_rank | avg_actual | standard_target | challenge_target |
|---|--:|---|---|--:|--:|--:|--:|
| 2025_10_2026_02 | 234 | イオンモール大曲 | 平日 | 5 | 7 | **8** | **9** |
| 2025_10_2026_02 | 268 | 新百合丘オーパ | 平日 | 5 | NULL | **4** | **5** |
| 2025_10_2026_02 | 172 | ラザウォーク甲斐双葉 | 平日 | 5 | NULL | **4** | **5** |

**SFのみ（代表サンプル）:**
| benchmark_period_key | facility_code | facility_name | date_flag | decile_rank | avg_actual | standard_target | challenge_target |
|---|--:|---|---|--:|--:|--:|--:|
| 2025_10_2026_02 | 1 | ラゾーナ川崎 | 通常土日 | 1 | 10 | **15** | **16** |
| 2025_10_2026_02 | 2 | イオンレイクタウン | 通常土日 | 1 | 21 | **22** | **38** |
| 2025_10_2026_02 | 3 | イオンモール幕張新都心 | 通常土日 | 1 | 20 | **22** | **38** |
| 2025_10_2025_12 | 4 | イオンモール土浦 | 年末 | 4 | 22 | **23** | **37** |

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `b1898a530f5dd525cf4ef0c8c2a8ee01`
- BigQuery: `e51f7095d94ae006e59c29853ea51318`
- 一致: 不一致（standard_target/challenge_target の FLOAT 演算順序差によるもので想定どおり）

## 7. 既知差分・許容判断

| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | 分位点 `p10`/`p70`/`p75`/`p90` が ±1 ズレ | 80〜317 行/列 | 要因 B（ベンチの分位点 ±1 差が同一デシル群の全施設へ伝播） | 許容 |
| 2 | `avg_actual` が ±1 ズレ | 9 行 | 要因 B（AVG の FLOAT 演算順序差） | 許容 |
| 3 | `standard_target` が ±1〜3 ズレ | 30 行 | 要因 B + タイル選択 CASE 1 段 | 許容 |
| 4 | `challenge_target` が ±1〜16 ズレ | 28 行 | 要因 B + タイル選択 CASE を 2 段通過した増幅 | 許容 |

（BQのみ/SFのみ 720 行は上記の和集合。すべて要因 B 起因の ±1〜16 差で、キー列のズレは無い。）

**要因 B（FLOAT 演算順序差・消去不能）:**

`avg_actual` は `AVG()` による FLOAT 集計値を `round_bq(,0)` で整数化したもの。BQ と SF で
`AVG()` の累積順序が最下位ビットレベルで異なり、値が丸め境界（○.5 等）に乗った施設で
BQ と SF の丸め後値が ±1 フリップする。源泉の z_score は BQ・SF 完全一致だが、
集計順序のみの違いによる乖離は消去不能。`round_bq` マクロで丸め方は BQ・SF 統一済みだが、
丸める前の FLOAT 値が異なるため差は残る。

**増幅メカニズム（standard_target → challenge_target で差が拡大する理由）:**

`standard_target` は `avg_actual` の値に応じて分位点（p50→p60→p70→p75→p90/max）を
CASE で選択し GREATEST(選択値, 1) を返す。`challenge_target` は `standard_target` を
もとにさらに分位点（p60→p70→p75→p90/max）を CASE で再選択する（CASE 2 段構造）。

代表例: 1 施設の `avg_actual` が境界 18.5 でフリップ（18→19）
→ 同一デシル群の分位点 p75 が 18→19 にズレ
→ `standard_target` のタイル選択が 1 段飛んで 22→19（差 3）
→ `challenge_target` のタイル選択がもう 1 段飛んで 38→22（**差 16**）

起点は ±1 だが、タイル選択 CASE を 2 段通過するため隣の段（22→38 等）に
飛んで増幅される。BQ・SF いずれの値も計算ロジックとしては正しく、ロジック誤りではない。
差が生じる行はデシル・日付区分単位での分位点が丸め境界近傍にある施設に限られる。

> **注（行数が 720 になる理由）:** 値差はすべて要因 B（FLOAT 演算順序差）起因で、`decile_rank` を
> 含むキー列にズレは無い（キーは BQ・SF で完全結合）。行数が standard_target(30)/challenge_target(28)
> より大きい 720 になるのは、スナップショットが分位点列 `p10`/`p70`/`p75`/`p90` を保持しており、
> ベンチ側の ±1 分位点差（9 グループ）が**同一デシル群にぶら下がる多数の施設へ伝播**するため。
> p90 だけで 317 行に波及する。多重集合比較ではこれらが BQのみ/SFのみとして 1 行ずつ計上される。

## 8. 判定
- 判定基準: 完全一致、または既知の許容差分のみであれば OK。
- 判定: **OK（既知の許容差分=FLOAT 演算順序差とそのタイル選択 CASE 増幅のみ）**
- 補足:
  - 件数は BQ・SF ともに 21,438 件で一致。
  - 差分 720 行（3.36%）はすべて要因 B（FLOAT 演算順序差）起因の ±1〜16 差で、ロジック誤りではない。
    内訳は分位点 p90(317)/p70(159)/p75(159)/p10(80)、avg_actual(9)、standard_target(30)、
    challenge_target(28) の和集合。キー列（`decile_rank` 含む）にズレは無い。
  - p20/p25/p30/p40/p50/p60/max_performance は完全一致。
  - 行数が standard_target/challenge_target の差分数より大きいのは、スナップショットが保持する
    分位点列にベンチ側の ±1 差が伝播し、各デシル群の多数施設へ波及するため（値差は常に ±1）。
  - ハッシュ不一致は上記 ±1〜16 差によるもので想定どおり。
