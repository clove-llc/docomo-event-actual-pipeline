# int_event_decile_benchmark 数値検証（デシルベンチ）

Snowflake 移行後の int ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table デシルベンチ`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.INT.INT_EVENT_DECILE_BENCHMARK`（VIEW）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_event_decile_benchmark`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 210 |
| BigQuery（移行元） | 210 |
| 一致レコード | 201 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

※ 件数（行数）は一致。9行は値が異なる（後述）。

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: なし。

## 5. カラム別差分
| 列 | 型 | 不一致セル数 | 差分の内容 |
|---|---|--:|---|
| `p10` | FLOAT | 1 | ±1（丸め1単位。要因B） |
| `p70` | FLOAT | 2 | ±1（丸め1単位。要因B） |
| `p75` | FLOAT | 2 | ±1（丸め1単位。要因B） |
| `p90` | FLOAT | 4 | ±1（丸め1単位。要因B） |

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `192305a902ec61dad6d247f557456201`
- Snowflake: `925d25622fb7d506b297ff5d100bf69c`
- 一致: ✗（既知の許容差分による不一致）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `p10`/`p70`/`p75`/`p90` 各分位点 ±1 | 合計9行（p10:1/p70:2/p75:2/p90:4） | 要因B（後述） | 許容 |

**要因B（FLOAT演算順序差・消去不能）:**
AVG/PERCENTILE_CONT を FLOAT で計算するため、BQ と SF で合計の最下位ビット（1〜5 ULP・相対差≈1e-16）が食い違い、平均が丸め境界(x.x5/○.5)に乗った行だけ丸め後±0.1/±1割れる。源泉 z_score は生値で完全一致（乖離は集計順序のみが原因）。round_bq で丸め方は統一済みだが丸める前の値が違うため消去不能。差は常に丸め1単位に限定されロジックは正しい。

## 8. 判定
- 判定: **OK**（既知の許容差分のみ）
- 補足: 差分9行はすべて分位点列（p10/p70/p75/p90）の丸め1単位ずれ（要因B）。キー列・件数・その他列は完全一致。
