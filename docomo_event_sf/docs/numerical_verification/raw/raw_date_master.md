# raw_date_master 数値検証

## 1. メタ情報
- 実施日: 2026-06-05
- 実施者: numerical-verification skill
- 検証コード: `cd docomo_event_sf && python tools/verify_code.py --table 日付マスタ --show-diff`

## 2. 対象
- 比較元（Snowflake）: `HARATO.RAW.RAW_DATE_MASTER`
- 比較先（BigQuery）: `digital-well-456700-i9.docomo_event_raw.raw_date_master`
- スコープ: 全件（16列）

## 3. 件数
| 区分 | 件数 |
|---|--:|
| Snowflake | 730 |
| BigQuery | 730 |
| 一致レコード | 730 |
| Snowflakeのみ | 0 |
| BigQueryのみ | 0 |

## 4. 比較方法・正規化
- 多重集合（Counter）で突合。
- 型統一のみ: num→float(小数9桁) / date→`YYYY-MM-DD` / bool→bool / str はそのまま。
- `#N/A` 等の Excel エラーは Python 側で NULL 吸収（本表では該当なし）。

## 5. カラム別差分
- **全16列一致**。

## 6. ハッシュ値（順序非依存・正規化後の多重集合 MD5）
- Snowflake: `6b358516c1ce0d4523373bef38c4233b`
- BigQuery: `6b358516c1ce0d4523373bef38c4233b`
- 一致: ✓

## 7. 既知差分・許容判断
- なし。

## 8. 判定
- 判定基準: 完全一致 or 既知の許容差分のみ → OK。
- 判定: **OK**
