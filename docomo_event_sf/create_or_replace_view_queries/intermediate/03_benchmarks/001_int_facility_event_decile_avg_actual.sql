create or replace view USERDB_B_P01_LAK.USER_SMCB_01.int_facility_event_decile_avg_actual as (
with joined as (
    select
        p.benchmark_period_key,
        p.benchmark_period_name,
        p.period_start_date,
        p.period_end_date,
        d.facility_code,
        d.facility_name,
        d.po_level,
        d.regional_office,
        d.branch_office,
        d.date_flag,
        m.decile_rank,
        d.actual
    from USERDB_B_P01_LAK.USER_SMCB_01.int_facility_daily_actual as d
    inner join USERDB_B_P01_LAK.USER_SMCB_01.RAW_BENCHMARK_PERIODS as p
        on d.date between p.period_start_date and p.period_end_date
    left join USERDB_B_P01_LAK.USER_SMCB_01.int_facility_event_decile_mapping as m
        on d.facility_code = m.facility_code
       and d.date_flag = m.date_flag
)
select
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    facility_code,
    facility_name,
    po_level,
    regional_office,
    branch_office,
    date_flag,
    decile_rank,
    count(*) as actual_days,
    sum(actual) as total_actual,
    round(avg(actual)) as avg_actual
from joined
group by
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    facility_code,
    facility_name,
    po_level,
    regional_office,
    branch_office,
    date_flag,
    decile_rank
);