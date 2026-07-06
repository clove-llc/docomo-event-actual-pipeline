# stg層 数値検証対象外テーブル

## 概要
以下の Snowflake stg ビューは BigQuery に対応するテーブルが存在しないため、数値検証の対象外。

## 対象外テーブル一覧
| Snowflake ビュー | 理由 |
|---|---|
| `DOCOMO_DB.STG.STG_FACILITY_SCHEDULE_CONSTRAINTS_MASTER` | SF固有の新機能用マスタ。BigQueryに対応テーブルが存在しないため数値検証の対象外。 |
| `DOCOMO_DB.STG.STG_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER` | SF固有の新機能用マスタ。BigQueryに対応テーブルが存在しないため数値検証の対象外。 |

## 備考
- これらのテーブルは Snowflake 移行時に新たに追加された機能（スケジュール制約管理）のためのマスタデータであり、BigQuery 側に移行元となるテーブルが存在しない。
- 数値検証は BQ↔SF の突合を前提とするため、BQ対応なしのSF固有テーブルは検証対象から除外する。
