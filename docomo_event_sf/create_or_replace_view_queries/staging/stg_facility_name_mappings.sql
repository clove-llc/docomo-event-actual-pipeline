
  create or replace   view HARATO.STG.stg_facility_name_mappings
  
  
  
  
  as (
    select
    "original_name" as "ORIGINAL_NAME",
    "mapped_name" as "MAPPED_NAME"
from HARATO.RAW.RAW_FACILITY_NAME_MAPPINGS
  );

