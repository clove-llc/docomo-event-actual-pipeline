# int_facility_target_cpa_by_facility 数値検証（施設別目標CPA）

Snowflake 移行後の int ビューが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-07-04
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `python tools/verify_code.py --table 施設別目標CPA`）

## 2. 対象
- 比較元（Snowflake）: `DOCOMO_DB.INT.INT_FACILITY_TARGET_CPA_BY_FACILITY`（VIEW）
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_target_cpa_by_facility`
- スコープ: 全件
- 比較列: BigQuery INFORMATION_SCHEMA から自動導出（BQカラムベース）。SF拡張列は比較対象外。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 639 |
| BigQuery（移行元） | 639 |
| 一致レコード | 638 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

※ 件数（行数）は一致。1行は値が異なる（後述）。

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。型表現差のみ吸収（num→float 9桁丸め / date→`YYYY-MM-DD` / bool→bool / str はtrimしない）。
- Excel エラー値（`#N/A` 等）は Python 側で NULL 吸収。
- 除外列: なし。

## 5. カラム別差分
| 列 | 型 | 不一致セル数 | 差分の内容（BQ値 / SF値） |
|---|---|--:|---|
| `cpa` | FLOAT | 1 | 施設「４プラ」: BQ=`46961.444444444…`（FLOAT64・無限精度） / SF=`46961.444444`（NUMBER系・小数6桁）。差≈4.4e-7（実質無害） |

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- BigQuery: `33d0a09f75257fd739aff927ebdf2348`
- Snowflake: `19cb7b9e1e0c00c954a8a6ff8aa26bfc`
- 一致: ✗（既知の許容差分による不一致）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `cpa` の小数桁差（施設「４プラ」のみ） | 1行 | SF VIEW の型設計（NUMBER系・小数6桁）による丸め桁差。BQ=FLOAT64（無限精度）との表現差。差≈4.4e-7・実質無害 | 許容（SF型設計差） |

※ 要因B（FLOAT演算順序差）ではなく、SF VIEW の NUMBER 型精度（小数6桁）による表現差。

## 8. 判定
- 判定: **OK**（既知の許容差分のみ）
- 補足: 差分1行は `cpa` 列の小数7桁以下の精度差（差≈4.4e-7）のみ。キー列・件数・その他列は完全一致。SF VIEW の型設計に起因する実質無害な差異。
