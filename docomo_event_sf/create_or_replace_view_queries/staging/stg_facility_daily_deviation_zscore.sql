
create or replace view HARATO.STG.stg_facility_daily_deviation_zscore as (
select
  * replace (
    z_score::number(38,10) as z_score
  )
from HARATO.RAW.raw_facility_daily_deviation_zscore
);

