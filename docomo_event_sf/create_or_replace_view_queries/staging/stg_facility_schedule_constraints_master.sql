
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_schedule_constraints_master
  
  
  
  
  as (
    select
    facility_code,
    trim(facility_name) as facility_name,
    monthly_event_limit,
    operating_days
from USERDB_B_P01_LAK.USER_SMCB_01.RAW_FACILITY_SCHEDULE_CONSTRAINTS_MASTER
  );

