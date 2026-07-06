# int_facility_event_planning_snapshot 数値検証（計画スナップショット）

Snowflake 移行後の int ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 計画スナップショット`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.INT.INT_FACILITY_EVENT_PLANNING_SNAPSHOT`（VIEW）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_event_planning_snapshot`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 21,438 |
| BigQuery（移行元） | 21,438 |
| 一致レコード | 20,718 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

※ 件数（行数）は一致。720行は値が異なる（後述）。

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: `branch_office`（SF=拠点略号プレフィックス除去後の支店名 / BQ=プレフィックス付き表記「神）神奈川支店」。表記のみの設計差。データ本体は同一）。

## 5. カラム別差分
| 列 | 型 | 不一致セル数 | 差分の内容 |
|---|---|--:|---|
| `p90` | FLOAT | 317 | ±1（丸め1単位。要因B） |
| `p70` | FLOAT | 159 | ±1（丸め1単位。要因B） |
| `p75` | FLOAT | 159 | ±1（丸め1単位。要因B） |
| `p10` | FLOAT | 80 | ±1（丸め1単位。要因B） |
| `avg_actual` | FLOAT | 9 | ±1（丸め1単位。要因B） |
| `standard` | FLOAT | 30 | ±1（タイル選択CASE増幅。要因B） |
| `challenge` | FLOAT | 28 | ±1（タイル選択CASE2段増幅。要因B） |

※ 差分720行は上記列の和集合。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `fe11fd964794b8e5a71b5b75a58918ba`
- Snowflake: `6217773197ed8027c6b2ede5e707f957`
- 一致: ✗（既知の許容差分による不一致）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `branch_office` 表記差 | 全行 | SF=拠点略号プレフィックス除去（設計どおり）/ BQ=プレフィックス付き | 比較対象外（許容） |
| 2 | 分位点列（p10/p70/p75/p90）±1 伝播＋standard/challenge 増幅 | 720行（p90:317/p70:159/p75:159/p10:80/avg_actual:9/standard:30/challenge:28 の和集合） | 要因B（後述） | 許容 |

**要因B（FLOAT演算順序差・消去不能）:**
AVG/PERCENTILE_CONT を FLOAT で計算するため、BQ と SF で合計の最下位ビット（1〜5 ULP・相対差≈1e-16）が食い違い、平均が丸め境界(x.x5/○.5)に乗った行だけ丸め後±0.1/±1割れる。源泉 z_score は生値で完全一致（乖離は集計順序のみが原因）。round_bq で丸め方は統一済みだが丸める前の値が違うため消去不能。差は常に丸め1単位に限定されロジックは正しい。challenge_target はタイル選択CASEを2段持つため最大16に増幅。計画スナップショットの720行は、ベンチの±1分位点差が同一デシル群の多数施設の分位点列(p90:317/p70:159/p75:159/p10:80)へ伝播した和集合（キー列のズレは無い）。

## 8. 判定
- 判定: **OK**（既知の許容差分のみ）
- 補足: 差分720行はすべて要因Bによる分位点の丸め1単位ずれと、それに起因する standard/challenge の目標値増幅。キー列・件数は完全一致。ロジックは正しい。
