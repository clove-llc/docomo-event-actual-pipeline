{#-
  s3: 施設別日付フラグ別_季節指数マスタ（偏差値版）＝最終成果物。
  ＝ dbt source raw_facility_daily_deviation_zscore 相当（long）。

  季節指数(z_score):
    - 偏差値 = (値 − 平均) / 標準偏差 × 10 + 50
    - v = ROUND(偏差値 / 50, 1)、 v<=0 なら 1
    - 実計算は4フラグ（平日/通常土日/三連休/飛び石祝日）のみ。他フラグ・std無し/0 は一律 1.0。
  month = MONTH(date)
  week_number_monthly = 月内週番号（月曜始まり。月初〜最初の日曜=第1週）
  date_flag = RAW_DATE_FLAG
-#}
{{ config(materialized='table') }}

{%- set idx_flags = ['平日', '通常土日', '三連休', '飛び石祝日'] -%}

with joined as (
    select
        d.facility_code,
        d.facility_name,
        d.event_date,
        d.sense_value,
        d.date_flag,
        s.mean_sense,
        s.std_sense
    from {{ ref('s1_int_seasonal_daily') }} d
    left join {{ ref('s2_int_seasonal_flag_stats') }} s
        on d.facility_code = s.facility_code
       and d.date_flag    = s.date_flag
),
calc as (
    select
        *,
        case
            when date_flag in ({% for f in idx_flags %}'{{ f }}'{{ "," if not loop.last }}{% endfor %})
                 and std_sense is not null and std_sense <> 0
            then round(((sense_value - mean_sense) / std_sense * 10 + 50) / 50, 1)
        end as v
    from joined
)
select
    event_date                                                                      as date,
    facility_code,
    facility_name,
    case when v is null or v <= 0 then 1.0 else v end                               as z_score,
    month(event_date)                                                               as month,
    floor((day(event_date) - 1 + (dayofweekiso(date_trunc('month', event_date)) - 1)) / 7) + 1
                                                                                    as week_number_monthly,
    date_flag
from calc
