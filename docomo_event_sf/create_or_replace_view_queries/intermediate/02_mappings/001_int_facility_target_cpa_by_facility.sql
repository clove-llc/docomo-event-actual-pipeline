
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.int_facility_target_cpa_by_facility
  
  
  
  
  as (
    select
  s_f_t.facility_name,
  avg(s_f_t.cpa) as cpa
from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_target_cpa_master as s_f_t
group by
  s_f_t.facility_name
  );

