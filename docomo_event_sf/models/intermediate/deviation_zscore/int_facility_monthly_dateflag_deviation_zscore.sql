{#-
  BQ int_facility_monthly_dateflag_deviation_zscore のミラー。
  施設×月×日付フラグ ごとの z_score 平均（週番号別の平均をさらに平均）。
-#}
select distinct
    f.facility_code,
    f.facility_name,
    f.month,
    f.date_flag,
    {{ round_bq('avg(avg_z_score)', 1) }} as avg_z_score
from {{ ref('int_facility_monthly_weekday_dateflag_deviation_zscore') }} as f
group by
    f.facility_code,
    f.facility_name,
    f.month,
    f.date_flag
