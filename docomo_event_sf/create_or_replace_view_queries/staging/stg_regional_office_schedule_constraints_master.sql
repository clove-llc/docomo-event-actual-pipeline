
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.stg_regional_office_schedule_constraints_master
  
  
  
  
  as (
    select
    regional_office,
    daily_event_limit,
    operating_days
from USERDB_B_P01_LAK.USER_SMCB_01.RAW_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER
  );

