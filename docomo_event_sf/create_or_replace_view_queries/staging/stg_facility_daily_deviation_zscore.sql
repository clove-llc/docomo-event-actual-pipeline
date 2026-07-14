
create or replace view USERDB_D_P01_LAK.USER_SMCB_01.stg_facility_daily_deviation_zscore as (
select
  *
from USERDB_D_P01_LAK.USER_SMCB_01.raw_facility_daily_deviation_zscore
);

