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
