
  create or replace   view HARATO.STG.stg_facility_foot_traffic_avg_and_decile_by_flag
  
  
  
  
  as (
    select *
from HARATO.RAW.raw_facility_foot_traffic_avg_and_decile_by_flag
  );

