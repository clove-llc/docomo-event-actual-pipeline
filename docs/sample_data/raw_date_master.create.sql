-- 源泉テーブル RAW_DATE_MASTER のサンプル DDL（HARATO.RAW.RAW_DATE_MASTER）
-- カレンダー日付マスタ（個人情報・施設情報なし）。カラム名は小文字クォート識別子。
-- latest_updated_at はアップローダ付与列（既定で現在時刻）。

create or replace TABLE RAW_DATE_MASTER (
	"date" DATE,
	"year_month" VARCHAR(16777216),
	"year" NUMBER(38,0),
	"month" NUMBER(38,0),
	"day" NUMBER(38,0),
	"week_number_yearly" NUMBER(38,0),
	"week_number_monthly" NUMBER(38,0),
	"weekday_name" VARCHAR(16777216),
	"weekday_name_and_week_number_monthly" VARCHAR(16777216),
	"weekday_holiday_weekend" VARCHAR(16777216),
	"is_offday" BOOLEAN,
	"holiday_name" VARCHAR(16777216),
	"is_holiday" BOOLEAN,
	"weekday_holiday_with_holiday" VARCHAR(16777216),
	"date_type" VARCHAR(16777216),
	"date_flag" VARCHAR(16777216),
	"latest_updated_at" TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- raw_date_master.csv のロード手順（検証済み: 730行 LOADED / エラー0 / 源泉と HASH_AGG 完全一致）
-- CSV 仕様: UTF-8(BOMなし) / LF改行 / ヘッダー1行 / 区切り "," / 文字列は必要時のみ " で囲む /
--           NULL=空欄 / BOOLEAN=TRUE|FALSE / DATE=YYYY-MM-DD / TIMESTAMP=YYYY-MM-DD HH24:MI:SS.FF
-- ============================================================================

-- 1) 再利用可能な FILE FORMAT を作成（任意。COPY にインラインで書いても可）
create or replace file format HARATO.RAW.FF_SAMPLE_CSV
  type = csv
  skip_header = 1
  field_delimiter = ','
  record_delimiter = '\n'
  field_optionally_enclosed_by = '"'
  null_if = ('')
  empty_field_as_null = true
  encoding = 'UTF8'
  timestamp_format = 'YYYY-MM-DD HH24:MI:SS.FF';

-- 2) ローカルCSVをテーブルステージへアップロード（SnowSQL/ドライバから実行）
--    PUT 'file:///absolute/path/to/raw_date_master.csv' @%RAW_DATE_MASTER OVERWRITE=TRUE AUTO_COMPRESS=FALSE;

-- 3) ロード（検証済みの設定）
-- COPY INTO HARATO.RAW.RAW_DATE_MASTER
--   FROM @%RAW_DATE_MASTER/raw_date_master.csv
--   FILE_FORMAT = (FORMAT_NAME = HARATO.RAW.FF_SAMPLE_CSV)
--   ON_ERROR = 'ABORT_STATEMENT';
--
-- ※ Snowsight の「Load data into table」UIから上記 FILE FORMAT 相当（ヘッダースキップ/UTF8/
--    フィールド囲み"/空欄=NULL）を選べば GUI でも同一結果でロード可能。
