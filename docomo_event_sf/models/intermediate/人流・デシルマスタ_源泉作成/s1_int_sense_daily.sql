{#-
  s1: 01_日別施設別（SENSE）を縦持ち化。施設×日 の SENSE 日次値（施設の日別パターン）を long に。
-#}
{{ config(materialized='table') }}

with src as (
    select t.*, object_construct(*) as obj
    from {{ source('raw', 'RAW_FACILITY_FOOT_TRAFFIC_DAILY') }} t
)
select
    src."施設コード"::number(38,0) as facility_code,
    src."施設名"::varchar         as facility_name,
    to_date(f.key)                as event_date,
    f.value::float                as sense_value
from src, lateral flatten(input => src.obj) f
where f.key rlike '[0-9]{4}-[0-9]{2}-[0-9]{2}'   -- 日付列のみ（施設コード/施設名/年間平均値/監査列は除外）
