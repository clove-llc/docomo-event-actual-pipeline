
  create or replace   view HARATO.INT.int_facility_target_cpa_by_facility
  
  
  
  
  as (
    select
  s_f_t.facility_name,
  avg(s_f_t.cpa) as cpa
from HARATO.STG.stg_facility_target_cpa_master as s_f_t
group by
  s_f_t.facility_name
  );

