
  create or replace   view USERDB_D_P01_LAK.USER_SMCB_01.stg_facility_name_mappings
  
  
  
  
  as (
    select
    "original_name" as "ORIGINAL_NAME",
    "mapped_name" as "MAPPED_NAME"
from USERDB_D_P01_LAK.USER_SMCB_01.RAW_FACILITY_NAME_MAPPINGS
  );

