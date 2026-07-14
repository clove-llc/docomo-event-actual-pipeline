
  create or replace   view USERDB_D_P01_LAK.USER_SMCB_01.int_facility_daily_actual
  
  
  
  
  as (
    select distinct
    f_m.facility_code,
    f_m.facility_name,
    f_m.po_level,
    f_m.regional_office,
    f_m.branch_office,
    d_m.date,
    d_m.year_month,
    d_m.week_number_monthly,
    d_m.week_number_yearly,
    d_m.weekday_name,
    d_m.weekday_holiday_with_holiday,
    d_m.date_type,
    d_m.date_flag,
    f_a.actual_value as actual
from USERDB_D_P01_LAK.USER_SMCB_01.stg_facility_master as f_m
inner join USERDB_D_P01_LAK.USER_SMCB_01.int_facility_actuals as f_a
    on f_m.facility_name = f_a.facility_name
left join USERDB_D_P01_LAK.USER_SMCB_01.stg_date_master as d_m
    on f_a.event_date = d_m.date
  );

