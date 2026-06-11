# int_facility_monthly_dateflag_deviation_zscore 数値検証（月フラグZ・中間層）

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `export SNOWFLAKE_ACCOUNT="WFJVSLU-VT27190" SNOWFLAKE_USER="DAISUKE_HARATO" SNOWFLAKE_ROLE="ACCOUNTADMIN" SNOWFLAKE_DATABASE="HARATO" SNOWFLAKE_WAREHOUSE="STREAMLIT_WH" SNOWFLAKE_PRIVATE_KEY_PATH="/Users/d.harato/.snowflake/clove_dcc.p8" && .venv/bin/python docomo_event_sf/tools/verify_code.py --table "月フラグZ" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_MONTHLY_DATEFLAG_DEVIATION_ZSCORE`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_monthly_dateflag_deviation_zscore`
- スコープ: 全件。キー列: `facility_code`, `month`, `date_flag`。集計列: `avg_z_score`（週平均 z_score を月・date_flag 単位でさらに平均した二段集計。`round_bq` で小数1桁丸め）。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 30,966 |
| BigQuery（移行元） | 30,966 |
| 一致レコード | 29,477 |
| Snowflakeのみ | 1,489 |
| BigQueryのみ | 1,489 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型表現差のみ吸収: num→float（小数9桁）/ date→`YYYY-MM-DD` / str はそのまま（trim しない）。
- `#N/A` は Python 側で NULL 吸収（該当列なし）。
- 除外列: なし（全列比較）。

## 5. カラム別差分
| 列 | 型 | 不一致行数 | 差分の内容 |
|---|---|--:|---|
| `avg_z_score` | FLOAT | 1,489（4.81%） | BQ値と SF値の差は常に **±0.1**（小数1桁丸め後の1段階のみ）。丸め前の生値（FLOAT AVG）の絶対差は最大 4.44e-16（マシンイプシロン級・最大 2 ULP）。 |

不一致サンプル（BQのみ側・先頭5件）:

| facility_code | facility_name | month | date_flag | avg_z_score（BQ） |
|---|---|--:|---|--:|
| 1 | ラゾーナ川崎 | 1 | 三連休 | 1.1 |
| 2 | イオンレイクタウン | 1 | 三連休 | 0.9 |
| 4 | イオンモール土浦 | 1 | 三連休 | 1.1 |
| 5 | イオンモール浦和美園 | 2 | 三連休 | 1.1 |
| 6 | ブルメール舞多聞 | 1 | 三連休 | 1.1 |

SFのみ側の同行は avg_z_score が ±0.1 ずれた値を持つ（キー・件数は完全一致）。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `c0f05b800fde3b42b64bae268c3d8e12`
- BigQuery:  `5820ab1a6b114042d2214249ab2b3bbe`
- 一致: 不一致（avg_z_score の ±0.1 差によるもの。想定どおり）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | `avg_z_score` が ±0.1 ずれる | 1,489（4.81%） | **FLOAT演算順序差（要因B）**: 二段集計（日次→週平均→月平均）を FLOAT で行うため、BQ と SF で合計の最下位ビット（小数16桁目、1〜2 ULP）が食い違う。源泉 z_score の生値は 289,810 行が完全一致（差 0）。乖離は集計の足し込み順序のみが原因。平均がちょうど丸め境界（x.x5）に乗った行だけ `round_bq` 後に ±0.1 割れる。差は常に ±0.1 に限定。月週版（週フラグZ 相当）より境界に乗る行が多いのは二段集計による累積誤差のため | **許容**（消去不能な浮動小数演算誤差。キー・件数・ロジックは正しい） |

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。それ以外は NG。
- 判定: **OK（既知の許容差分のみ）**
- 補足: キーと件数（30,966件）は BQ/SF 完全一致。差分 1,489 行（4.81%）はすべて `avg_z_score` の ±0.1 のみで、FLOAT 二段集計における丸め境界乗り上げ（マシンイプシロン級・最大 2 ULP）が原因。`round_bq` マクロで丸め方式は統一済みだが丸める前の値が異なるため消去不能。ロジック・集計ルールの誤りではなく、BQ/SF 間の浮動小数演算順序差のみによる既知許容差分と判断する。
