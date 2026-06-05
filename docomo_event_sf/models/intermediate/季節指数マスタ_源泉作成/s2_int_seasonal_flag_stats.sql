{#-
  s2: 平均値 / 標準偏差。施設×日付フラグ別の平均と標準偏差（標本=STDDEV_SAMP）。
  Excel: AVERAGEIF / STDEV（n-1）。実計算対象は4フラグ（平日/通常土日/三連休/飛び石祝日）だが、
  ここでは全フラグ分を算出し、下流で4フラグのみ採用する。
-#}
{{ config(materialized='table') }}

select
    facility_code,
    date_flag,
    avg(sense_value)         as mean_sense,
    stddev_samp(sense_value) as std_sense
from {{ ref('s1_int_seasonal_daily') }}
where date_flag is not null
group by facility_code, date_flag
