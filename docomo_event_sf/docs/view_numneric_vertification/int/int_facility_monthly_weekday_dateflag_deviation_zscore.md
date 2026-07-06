# int_facility_monthly_weekday_dateflag_deviation_zscore 数値検証（月週フラグZ）

Snowflake 移行後の int ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 月週フラグZ`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.INT.INT_FACILITY_MONTHLY_WEEKDAY_DATEFLAG_DEVIATION_ZSCORE`（VIEW）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_monthly_weekday_dateflag_deviation_zscore`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 96,074 |
| BigQuery（移行元） | 96,074 |
| 一致レコード | 95,491 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

※ 件数（行数）は一致。583行は値が異なる（後述）。

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: なし。

## 5. カラム別差分
| 列 | 型 | 不一致セル数 | 差分の内容 |
|---|---|--:|---|
| `avg_z_score` | FLOAT | 583 | ±0.1（丸め1単位。要因B） |

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `028074f0112bc3c576016fa2022d6f5b`
- Snowflake: `b3381495bc4296f6812ca0a749b73528`
- 一致: ✗（既知の許容差分による不一致）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `avg_z_score` ±0.1 | 583行 | 要因B（後述） | 許容 |

**要因B（FLOAT演算順序差・消去不能）:**
AVG/PERCENTILE_CONT を FLOAT で計算するため、BQ と SF で合計の最下位ビット（1〜5 ULP・相対差≈1e-16）が食い違い、平均が丸め境界(x.x5/○.5)に乗った行だけ丸め後±0.1/±1割れる。源泉 z_score は生値で完全一致（乖離は集計順序のみが原因）。round_bq で丸め方は統一済みだが丸める前の値が違うため消去不能。差は常に丸め1単位に限定されロジックは正しい。

## 8. 判定
- 判定: **OK**（既知の許容差分のみ）
- 補足: 差分583行はすべて `avg_z_score` の ±0.1 ずれ（要因B）。キー列・件数・その他列は完全一致。
