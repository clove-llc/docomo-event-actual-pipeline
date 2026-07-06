create or replace view HARATO.RAW.raw_facility_foot_traffic_avg_and_decile_by_flag as
(
    with
-- s1: 01_日別施設別（SENSE）を縦持ち化（施設×日 の SENSE 日次値）
sense_src as (
    select t.*, object_construct(*) as obj
    from HARATO.RAW.RAW_FACILITY_FOOT_TRAFFIC_DAILY t
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
    join HARATO.RAW.RAW_KDDI_FOOT_TRAFFIC k
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
    left join HARATO.RAW.RAW_DATE_FLAG df
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
    facility_name,round(max(case when date_flag = 'GW' then foot_traffic_avg end)) as gw_foot_traffic_avg,round(max(case when date_flag = 'お盆' then foot_traffic_avg end)) as obon_foot_traffic_avg,round(max(case when date_flag = '三連休' then foot_traffic_avg end)) as three_day_holiday_foot_traffic_avg,round(max(case when date_flag = '正月' then foot_traffic_avg end)) as new_year_foot_traffic_avg,round(max(case when date_flag = '通常土日' then foot_traffic_avg end)) as regular_weekend_foot_traffic_avg,round(max(case when date_flag = '年末' then foot_traffic_avg end)) as year_end_foot_traffic_avg,round(max(case when date_flag = '飛び石祝日' then foot_traffic_avg end)) as bridge_holiday_foot_traffic_avg,round(max(case when date_flag = '平日' then foot_traffic_avg end)) as weekday_foot_traffic_avg,round(max(case when date_flag = 'ブラックフライデー' then foot_traffic_avg end)) as black_friday_foot_traffic_avg,
    max(case when date_flag = 'GW' then decile_rank end) as gw_decile_rank,
    max(case when date_flag = 'お盆' then decile_rank end) as obon_decile_rank,
    max(case when date_flag = '三連休' then decile_rank end) as three_day_holiday_decile_rank,
    max(case when date_flag = '正月' then decile_rank end) as new_year_decile_rank,
    max(case when date_flag = '通常土日' then decile_rank end) as regular_weekend_decile_rank,
    max(case when date_flag = '年末' then decile_rank end) as year_end_decile_rank,
    max(case when date_flag = '飛び石祝日' then decile_rank end) as bridge_holiday_decile_rank,
    max(case when date_flag = '平日' then decile_rank end) as weekday_decile_rank,
    max(case when date_flag = 'ブラックフライデー' then decile_rank end) as black_friday_decile_rank
from deciled
group by facility_code, facility_name
)