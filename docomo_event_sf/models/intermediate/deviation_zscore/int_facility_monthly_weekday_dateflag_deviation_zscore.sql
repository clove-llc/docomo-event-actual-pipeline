{#-
  BQ int_facility_monthly_weekday_dateflag_deviation_zscore のミラー。
  施設×月×月内週番号×日付フラグ ごとの z_score 平均。
-#}
select
    f.facility_code,
    f.facility_name,
    f_d_z.month,
    f_d_z.week_number_monthly,
    f_d_z.date_flag,
    round(avg(f_d_z.z_score), 1) as avg_z_score
from {{ ref('stg_facility_daily_deviation_zscore') }} as f_d_z
left join {{ ref('stg_facility_master') }} as f
    on f_d_z.facility_code = f.facility_code
group by
    f.facility_code,
    f.facility_name,
    f_d_z.month,
    f_d_z.week_number_monthly,
    f_d_z.date_flag
