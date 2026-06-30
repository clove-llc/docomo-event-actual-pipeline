
  create or replace   view HARATO.STG.stg_facility_actuals
  
  
  
  
  as (
    select
    * exclude (facility_name),
    trim(facility_name) as facility_name
from HARATO.RAW.raw_facility_actuals
  );

