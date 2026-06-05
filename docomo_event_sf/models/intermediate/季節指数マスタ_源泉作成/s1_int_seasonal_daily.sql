{#-
  s1: 01_日別施設別（SENSE）を縦持ち化し、日付フラグを付与。
  施設×日 の SENSE 日次値 ＋ date_flag。
-#}
{{ config(materialized='table') }}

with src as (
    select t.*, object_construct(*) as obj
    from {{ source('raw', 'RAW_FACILITY_SEASONAL_DAILY') }} t
),
unpivoted as (
    select
        src."施設コード"::number(38,0) as facility_code,
        src."施設名"::varchar         as facility_name,
        to_date(f.key)                as event_date,
        f.value::float                as sense_value
    from src, lateral flatten(input => src.obj) f
    where f.key rlike '[0-9]{4}-[0-9]{2}-[0-9]{2}'
)
select
    u.facility_code,
    u.facility_name,
    u.event_date,
    u.sense_value,
    df."date_flag" as date_flag
from unpivoted u
left join {{ source('raw', 'RAW_DATE_FLAG') }} df
    on u.event_date = df."date"
