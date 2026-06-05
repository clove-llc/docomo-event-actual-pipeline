{#-
  s5: 施設&日付フラグ別_人流（平均）。フラグ別に AVG(人流)。
  Excel: SUMIFS(人流, フラグ=TRUE) / COUNTIFS(...)。
-#}
{{ config(materialized='table') }}

select
    facility_code,
    facility_name,
    date_flag,
    avg(foot_traffic) as foot_traffic_avg
from {{ ref('s4_int_facility_daily_flagged') }}
where date_flag is not null
group by facility_code, facility_name, date_flag
