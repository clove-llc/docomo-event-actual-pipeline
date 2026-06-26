
  create or replace   view HARATO.STG.stg_excluded_facility_master
  
  
  
  
  as (
    select
    trim(facility_name) as facility_name
from HARATO.RAW.RAW_EXCLUDED_FACILITY_MASTER
  );

