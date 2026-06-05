{#-
  s3: 03_日別数値（KDDI人流データをもとに）。KDDI年間人流(全日TTL) × 日別構成比 ＝ 日別の推定人流。
  Excel: C2=VLOOKUP(施設コード, KDDI), D2=C2 × '02'!構成比。
-#}
{{ config(materialized='table') }}

select
    r.facility_code,
    r.facility_name,
    r.event_date,
    k."foot_traffic_total" * r.daily_ratio as foot_traffic
from {{ ref('s2_int_sense_daily_ratio') }} r
join {{ source('raw', 'RAW_KDDI_FOOT_TRAFFIC') }} k
    on r.facility_code = k."facility_code"
