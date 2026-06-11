# int_facility_monthly_weekday_dateflag_deviation_zscore 数値検証

Snowflake 移行後の intermediate テーブルが、移行元 BigQuery と数値的に一致するかの検証記録。

## 1. メタ情報
- 実施日: 2026-06-10
- 実施者: numerical-verification skill
- 検証コード: `docomo_event_sf/tools/verify_code.py`（再現コマンド: `.venv/bin/python docomo_event_sf/tools/verify_code.py --table "月週フラグZ" --show-diff`）

## 2. 対象
- 比較元（Snowflake）: `HARATO.INT.INT_FACILITY_MONTHLY_WEEKDAY_DATEFLAG_DEVIATION_ZSCORE`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_intermediate.int_facility_monthly_weekday_dateflag_deviation_zscore`
- スコープ: 全件。キー: facility_code / month / week_number_monthly / date_flag。集計列: `avg_z_score = round_bq(avg(z_score), 1)`。
- 源泉: `stg_facility_daily_deviation_zscore`（SF/BQ ともに完全一致済み・289,810行）を GROUP BY して AVG → round_bq で小数1桁丸め。

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 96,074 |
| BigQuery（移行元） | 96,074 |
| 一致レコード | 95,491 |
| Snowflakeのみ（移行元に無い） | 583 |
| BigQueryのみ（Snowに無い） | 583 |

## 4. 比較方法・正規化
- 比較方法: **多重集合**（Counter による行レベル突合）。
- 列型は BQ スキーマから自動導出（`bq_column_types()` を使用）。
- 型表現差のみ吸収: num→float（小数9桁丸め）/ date→`YYYY-MM-DD` / bool→bool / str はそのまま（trim しない）。
- Excel エラー（`#N/A` 等）は Python 側で NULL に吸収（本テーブルは該当なし）。
- 除外列: **なし**（全列比較対象）。

## 5. カラム別差分
| 列 | 型 | 不一致行数 | 差分の内容 |
|---|---|--:|---|
| avg_z_score | FLOAT | 583 | 差は常に ±0.1（小数第1位丸め後のみ乖離）。BQのみ/SFのみ各583行。例: BQ=1.1 / SF=1.2、BQ=0.9 / SF=1.0 等。|

不一致サンプル（BQのみ）:
- `{facility_code: 6, 施設名: ブルメール舞多聞, month: 1, week: 2, date_flag: 三連休, avg_z_score: 1.1}`
- `{facility_code: 50, 施設名: セブンパーク天美, month: 1, week: 3, date_flag: 平日, avg_z_score: 0.9}`
- `{facility_code: 184, 施設名: ゆめシティ, month: 1, week: 3, date_flag: 平日, avg_z_score: 0.9}`
- `{facility_code: 187, 施設名: ゆめタウン夢彩都, month: 1, week: 3, date_flag: 平日, avg_z_score: 1.2}`
- `{facility_code: 202, 施設名: 小田原シティモールフレスポ, month: 1, week: 3, date_flag: 平日, avg_z_score: 0.9}`

不一致サンプル（SFのみ）:
- `{facility_code: 1480, 施設名: リヴィンオズ大泉, month: 9, week: 3, date_flag: 平日, avg_z_score: 0.7}`
- `{facility_code: 1206, 施設名: ビビット南船橋, month: 7, week: 5, date_flag: 平日, avg_z_score: 1.0}`
- `{facility_code: 1480, 施設名: リヴィンオズ大泉, month: 7, week: 4, date_flag: 平日, avg_z_score: 1.1}`
- `{facility_code: 1422, 施設名: マチノマ大森, month: 9, week: 3, date_flag: 平日, avg_z_score: 1.1}`
- `{facility_code: 1477, 施設名: イオン板橋ショッピングセンター, month: 2, week: 3, date_flag: 平日, avg_z_score: 1.0}`

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `b3381495bc4296f6812ca0a749b73528`
- BigQuery: `028074f0112bc3c576016fa2022d6f5b`
- 一致: 不一致（想定どおり。avg_z_score 差583行を反映）

## 7. 既知差分・許容判断
| # | 差分内容 | 件数 | 原因 | 対応 |
|---|---|--:|---|:--:|
| 1 | avg_z_score が ±0.1 乖離 | 583行 | FLOAT 演算順序差（IEEE754 加算の非結合性）。BQ・SF でグループ内の z_score 合計の最下位ビット（ULP 1〜2 桁、絶対差 4.44e-16・相対差 3.76e-16）が異なり、丸め境界（x.x5）に乗った群だけ round_bq 後に ±0.1 割れる。源泉 z_score は 289,810 行が完全一致しており、乖離は集計エンジンの足し込み順序のみが原因。round_bq で丸め方は統一済みだが、丸める前の浮動小数点値が異なるため消去不能。 | 許容（既知・ロジック正常） |

## 8. 判定
- 判定基準: 完全一致、または既知の許容差分のみであれば OK。それ以外は NG。
- 判定: **OK（既知の許容差分=FLOAT演算順序差のみ）**
- 補足: キー・件数（96,074行）は完全一致。avg_z_score の差 583行（0.61%）はすべて ±0.1 の丸め境界割れであり、BQ・SF 間の IEEE754 FLOAT 加算順序差に起因する消去不能な差分。源泉データ・ロジック・キーに問題はなく、許容差分として OK 判定とする。
