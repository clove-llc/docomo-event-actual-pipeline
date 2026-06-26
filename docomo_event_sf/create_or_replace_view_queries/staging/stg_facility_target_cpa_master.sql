
  create or replace   view HARATO.STG.stg_facility_target_cpa_master
  
  
  
  
  as (
    select
    replace(trim(facility_name), '・', '･') as facility_name,
    cpa
from HARATO.RAW.RAW_FACILITY_TARGET_CPA_MASTER
  );

