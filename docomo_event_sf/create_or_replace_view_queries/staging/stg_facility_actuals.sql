
  create or replace   view USERDB_D_P01_LAK.USER_SMCB_01.stg_facility_actuals
  
  
  
  
  as (
    select
    * exclude (facility_name),
    trim(facility_name) as facility_name
from USERDB_D_P01_LAK.USER_SMCB_01.raw_facility_actuals
  );

