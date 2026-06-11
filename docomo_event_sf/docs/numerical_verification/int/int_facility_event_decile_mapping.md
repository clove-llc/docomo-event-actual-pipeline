# int_facility_event_decile_mapping 数値検証（デシルマッピング・中間層）

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `export SNOWFLAKE_ACCOUNT="WFJVSLU-VT27190" SNOWFLAKE_USER="DAISUKE_HARATO" SNOWFLAKE_ROLE="ACCOUNTADMIN" SNOWFLAKE_DATABASE="HARATO" SNOWFLAKE_WAREHOUSE="STREAMLIT_WH" SNOWFLAKE_PRIVATE_KEY_PATH="/Users/d.harato/.snowflake/clove_dcc.p8" && .venv/bin/python docomo_event_sf/tools/verify_code.py --table "デシルマッピング" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_EVENT_DECILE_MAPPING`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_event_decile_mapping`
- スコープ: 全件・除外列なし（全列比較）。施設×日付フラグ→デシル区分のマッピングテーブル。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 7,146 |
| BigQuery（移行元） | 7,146 |
| 一致レコード | 7,146 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型表現差のみ吸収: num→float（小数9桁） / date→`YYYY-MM-DD` / str はそのまま（trim しない）。
- `#N/A` 等の Excel エラー値は Python 側で NULL 吸収。
- 除外列なし（全列を比較対象とした）。

## 5. カラム別差分
- 全列一致。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `f3c8619819956ae3e410dfbb56a71680`
- BigQuery:  `f3c8619819956ae3e410dfbb56a71680`
- 一致: ✓

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| - | なし | 0 | - | - |

除外列なし。差分なし。

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
- 補足: 7,146件すべてが一致。除外列なしの全列比較でハッシュ完全一致（`f3c8619…`）。FLOAT集計を含まない整数・文字・区分フラグのみの構成であり、予想どおり差分ゼロ。
