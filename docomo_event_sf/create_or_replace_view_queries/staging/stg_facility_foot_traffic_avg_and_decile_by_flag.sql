
create or replace view USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag as (
select
  *
from USERDB_B_P01_LAK.USER_SMCB_01.raw_facility_foot_traffic_avg_and_decile_by_flag
);

