create or replace view HARATO.RAW.raw_facility_daily_deviation_zscore as (
    with
-- s1: 01_日別施設別（SENSE）を縦持ち化し、日付フラグを付与
seasonal_src as (
    select t.*, object_construct(*) as obj
    from HARATO.RAW.RAW_FACILITY_FOOT_TRAFFIC_DAILY t
),
seasonal_unpivoted as (
    select
        src."施設コード"::number(38,0) as facility_code,
        src."施設名"::varchar         as facility_name,
        to_date(f.key)                as event_date,
        f.value::float                as sense_value
    from seasonal_src src, lateral flatten(input => src.obj) f
    where f.key rlike '[0-9]{4}-[0-9]{2}-[0-9]{2}'
),
seasonal_daily as (
    select
        u.facility_code,
        u.facility_name,
        u.event_date,
        u.sense_value,
        df."date_flag" as date_flag
    from seasonal_unpivoted u
    left join HARATO.RAW.RAW_DATE_FLAG df
        on u.event_date = df."date"
),
-- s2: 平均値 / 標準偏差（標本=STDDEV_SAMP）。全フラグ分を算出し、下流で4フラグのみ採用
seasonal_flag_stats as (
    select
        facility_code,
        date_flag,
        avg(sense_value)         as mean_sense,
        stddev_samp(sense_value) as std_sense
    from seasonal_daily
    where date_flag is not null
    group by facility_code, date_flag
),
-- s3: 偏差値 → 季節指数
joined as (
    select
        d.facility_code,
        d.facility_name,
        d.event_date,
        d.sense_value,
        d.date_flag,
        s.mean_sense,
        s.std_sense
    from seasonal_daily d
    left join seasonal_flag_stats s
        on d.facility_code = s.facility_code
       and d.date_flag    = s.date_flag
),
calc as (
    select
        *,
        case
            when date_flag in ('平日','通常土日','三連休','飛び石祝日')
                 and std_sense is not null and std_sense <> 0
            then round(((sense_value - mean_sense) / std_sense * 10 + 50) / 50, 1)
        end as v
    from joined
)
select
    event_date                                                                      as date,
    facility_code,
    facility_name,
    case when v is null or v <= 0 then 1.0 else v end                               as z_score,
    month(event_date)                                                               as month,
    floor((day(event_date) - 1 + (dayofweekiso(date_trunc('month', event_date)) - 1)) / 7) + 1
                                                                                    as week_number_monthly,
    date_flag
from calc
)