
  create or replace   view HARATO.STG.stg_facility_daily_deviation_zscore
  
  
  
  
  as (
    select *
from HARATO.RAW.raw_facility_daily_deviation_zscore
  );

