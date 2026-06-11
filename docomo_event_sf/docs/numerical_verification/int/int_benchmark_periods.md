# int_benchmark_periods 数値検証（ベンチ期間）

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table ベンチ期間`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_BENCHMARK_PERIODS`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_benchmark_periods`
- スコープ: 全件（3行のベンチマーク期間定義・固定値 UNION ALL）

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 3 |
| BigQuery（移行元） | 3 |
| 一致レコード | 3 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（date→`YYYY-MM-DD` / num→float / bool→bool / str はそのまま）。
- trim・`#N/A` 吸収・過度な丸めは行わない。列名は小文字化して突合（値の大小文字は変えない）。
- 比較から外した列: なし（除外列なし）。

## 5. カラム別差分
- **全列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `bf07acaddbe91183849619e1bff9097a`
- BigQuery: `bf07acaddbe91183849619e1bff9097a`
- 一致: ✓

## 7. 既知差分・許容判断
- 差分なし。除外列なし。

## 8. 判定
- 判定: **OK**（完全一致）
- 補足: 3行の固定値定義テーブル。件数・内容・ハッシュすべて一致。
