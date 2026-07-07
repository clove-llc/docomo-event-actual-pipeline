{#-
  BQ int_facility_event_decile_avg_actual のミラー。
  日別実績をベンチマーク期間で絞り、施設×日付フラグ×デシル区分の平均実績を算出。
-#}
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
    from {{ ref('int_facility_daily_actual') }} as d
    inner join {{ source('raw', 'RAW_BENCHMARK_PERIODS') }} as p
        on d.date between p.period_start_date and p.period_end_date
    left join {{ ref('int_facility_event_decile_mapping') }} as m
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
    {{ round_bq('avg(cast(actual as float))', 0) }} as avg_actual  -- BQ は AVG(INT64)→FLOAT64。型を合わせる
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
