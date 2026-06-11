{#-
  日付マスタ staging。BQ: SELECT * FROM raw_date_master のミラー。
  源泉切替: SF source('raw','RAW_DATE_MASTER')。latest_updated_at は除外。
  SF RAW は小文字クォート識別子のため、下流を清潔にする目的でカラム名を大文字へ正規化する。
-#}
select
    "date" as "DATE",
    "year_month" as "YEAR_MONTH",
    "year" as "YEAR",
    "month" as "MONTH",
    "day" as "DAY",
    "week_number_yearly" as "WEEK_NUMBER_YEARLY",
    "week_number_monthly" as "WEEK_NUMBER_MONTHLY",
    "weekday_name" as "WEEKDAY_NAME",
    "weekday_name_and_week_number_monthly" as "WEEKDAY_NAME_AND_WEEK_NUMBER_MONTHLY",
    "weekday_holiday_weekend" as "WEEKDAY_HOLIDAY_WEEKEND",
    "is_offday" as "IS_OFFDAY",
    "holiday_name" as "HOLIDAY_NAME",
    "is_holiday" as "IS_HOLIDAY",
    "weekday_holiday_with_holiday" as "WEEKDAY_HOLIDAY_WITH_HOLIDAY",
    "date_type" as "DATE_TYPE",
    "date_flag" as "DATE_FLAG"
from {{ source('raw', 'RAW_DATE_MASTER') }}
