
  create or replace   view HARATO.STG.stg_regional_office_schedule_constraints_master
  
  
  
  
  as (
    select
    regional_office,
    daily_event_limit,
    operating_days
from HARATO.RAW.RAW_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER
  );

