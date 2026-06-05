{#-
  s4: 04_日別数値（縦持ち）。日別人流に日付フラグ（GW/正月…）を付与。
  Excel: VLOOKUP(日付, 日付フラグマスタ)。日付マスタは暦2025を全カバーしないため
  フラグ源は RAW_DATE_FLAG（2024–2027）を使用。
-#}
{{ config(materialized='table') }}

select
    f.facility_code,
    f.facility_name,
    f.event_date,
    f.foot_traffic,
    df."date_flag" as date_flag
from {{ ref('s3_int_facility_daily_foot_traffic') }} f
left join {{ source('raw', 'RAW_DATE_FLAG') }} df
    on f.event_date = df."date"
