
  create or replace   view HARATO.STG.stg_facility_schedule_constraints_master
  
  
  
  
  as (
    select
    facility_code,
    trim(facility_name) as facility_name,
    monthly_event_limit,
    operating_days
from HARATO.RAW.RAW_FACILITY_SCHEDULE_CONSTRAINTS_MASTER
  );

