{#-
  人流・デシルマスタ源泉（＝ dbt source raw_facility_foot_traffic_avg_and_decile_by_flag 相当）。
  SENSE → 構成比 → 日別人流(KDDI×比) → フラグ付与 → 平均 → デシルランク の全工程を1モデルにまとめる。
  各工程はCTEで表現（中間テーブルは作らない）。施設ごとに 9フラグの「人流平均」と「デシル区分(1–10)」を横持ちで出力。

  デシル: Excel = CEILING(順位 / (施設数/10))。順位 = RANK.EQ(平均, desc)（1=最大）。
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

with
-- s1: 01_日別施設別（SENSE）を縦持ち化（施設×日 の SENSE 日次値）
sense_src as (
    select t.*, object_construct(*) as obj
    from {{ source('raw', 'RAW_FACILITY_FOOT_TRAFFIC_DAILY') }} t
),
sense_daily as (
    select
        src."施設コード"::number(38,0) as facility_code,
        src."施設名"::varchar         as facility_name,
        to_date(f.key)                as event_date,
        f.value::float                as sense_value
    from sense_src src, lateral flatten(input => src.obj) f
    where f.key rlike '[0-9]{4}-[0-9]{2}-[0-9]{2}'   -- 日付列のみ（施設コード/施設名/年間平均値/監査列は除外）
),
-- s2: 02_施設別日別構成比（各日の SENSE ÷ 施設の年間合計）
sense_daily_ratio as (
    select
        facility_code,
        facility_name,
        event_date,
        sense_value,
        div0(sense_value, sum(sense_value) over (partition by facility_code)) as daily_ratio
    from sense_daily
),
-- s3: 03_日別数値（KDDI年間人流(全日TTL) × 日別構成比 ＝ 日別推定人流）
daily_foot_traffic as (
    select
        r.facility_code,
        r.facility_name,
        r.event_date,
        k."foot_traffic_total" * r.daily_ratio as foot_traffic
    from sense_daily_ratio r
    join {{ source('raw', 'RAW_KDDI_FOOT_TRAFFIC') }} k
        on r.facility_code = k."facility_code"
),
-- s4: 04_日別数値（日付フラグ付与）。フラグ源は RAW_DATE_FLAG（2024–2027 全カバー）
daily_flagged as (
    select
        f.facility_code,
        f.facility_name,
        f.event_date,
        f.foot_traffic,
        df."date_flag" as date_flag
    from daily_foot_traffic f
    left join {{ source('raw', 'RAW_DATE_FLAG') }} df
        on f.event_date = df."date"
),
-- s5: 施設&日付フラグ別_人流（平均）。Excel: SUMIFS / COUNTIFS
flag_foot_traffic_avg as (
    select
        facility_code,
        facility_name,
        date_flag,
        avg(foot_traffic) as foot_traffic_avg
    from daily_flagged
    where date_flag is not null
    group by facility_code, facility_name, date_flag
),
-- s6: デシルランク（平均値ベース）
ranked as (
    select
        facility_code,
        facility_name,
        date_flag,
        foot_traffic_avg,
        rank() over (partition by date_flag order by foot_traffic_avg desc) as rnk,
        count(*) over (partition by date_flag)                              as n
    from flag_foot_traffic_avg
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
