
  create or replace   view HARATO.INT.int_facility_monthly_dateflag_deviation_zscore
  
  
  
  
  as (
select distinct
    f.facility_code,
    f.facility_name,
    f.month,
    f.date_flag,
    round(avg(avg_z_score), 1) as avg_z_score
from HARATO.INT.int_facility_monthly_weekday_dateflag_deviation_zscore as f
group by
    f.facility_code,
    f.facility_name,
    f.month,
    f.date_flag
  );

