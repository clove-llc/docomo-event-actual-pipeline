{#-
  s6: 施設&日付フラグ別_デシルランク（平均値ベース）＝最終成果物。
  施設ごとに 9フラグの「人流平均」と「デシル区分(1–10)」を横持ちで出力。
  デシル: Excel = CEILING(順位 / (施設数/10))。順位 = RANK.EQ(平均, desc)（1=最大）。
  出力列は dbt source raw_facility_foot_traffic_avg_and_decile_by_flag に準拠。
-#}
{{ config(materialized='table') }}

{%- set flags = [
    ('GW', 'gw'),
    ('お盆', 'obon'),
    ('三連休', 'three_day_holiday'),
    ('正月', 'new_year'),
    ('通常土日', 'regular_weekend'),
    ('年末', 'year_end'),
    ('飛び石祝日', 'bridge_holiday'),
    ('平日', 'weekday'),
    ('ブラックフライデー', 'black_friday'),
] -%}

with ranked as (
    select
        facility_code,
        facility_name,
        date_flag,
        foot_traffic_avg,
        rank() over (partition by date_flag order by foot_traffic_avg desc) as rnk,
        count(*) over (partition by date_flag)                              as n
    from {{ ref('s5_int_facility_flag_foot_traffic_avg') }}
),
deciled as (
    select
        facility_code,
        facility_name,
        date_flag,
        foot_traffic_avg,
        ceil(rnk / (n / 10.0)) as decile_rank   -- CEILING(順位 / (施設数/10))
    from ranked
)
select
    facility_code,
    facility_name,
    {%- for jp, en in flags %}
    {#- 平均は整数丸めで出力（Excelのデシルシート＝ROUND(SUMIFS/COUNTIFS)）。デシルは丸め前の順位で算出 -#}
    round(max(case when date_flag = '{{ jp }}' then foot_traffic_avg end)) as {{ en }}_foot_traffic_avg,
    {%- endfor %}
    {%- for jp, en in flags %}
    max(case when date_flag = '{{ jp }}' then decile_rank end) as {{ en }}_decile_rank{{ "," if not loop.last }}
    {%- endfor %}
from deciled
group by facility_code, facility_name
