
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_target_cpa_master
  
  
  
  
  as (
    select
    replace(trim(facility_name), '・', '･') as facility_name,
    cpa
from USERDB_B_P01_LAK.USER_SMCB_01.RAW_FACILITY_TARGET_CPA_MASTER
  );

