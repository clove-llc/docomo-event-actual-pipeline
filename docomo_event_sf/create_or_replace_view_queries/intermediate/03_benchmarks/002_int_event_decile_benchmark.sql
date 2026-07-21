
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.int_event_decile_benchmark
  
  
  
  
  as (
select
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    date_flag,
    decile_rank,
    round(round(percentile_cont(0.10) within group (order by avg_actual), 2)) as p10,
    round(round(percentile_cont(0.20) within group (order by avg_actual), 2)) as p20,
    round(round(percentile_cont(0.25) within group (order by avg_actual), 2)) as p25,
    round(round(percentile_cont(0.30) within group (order by avg_actual), 2)) as p30,
    round(round(percentile_cont(0.40) within group (order by avg_actual), 2)) as p40,
    round(round(percentile_cont(0.50) within group (order by avg_actual), 2)) as p50,
    round(round(percentile_cont(0.60) within group (order by avg_actual), 2)) as p60,
    round(round(percentile_cont(0.70) within group (order by avg_actual), 2)) as p70,
    round(round(percentile_cont(0.75) within group (order by avg_actual), 2)) as p75,
    round(round(percentile_cont(0.90) within group (order by avg_actual), 2)) as p90,
    max(avg_actual) as max_performance
from USERDB_B_P01_LAK.USER_SMCB_01.int_facility_event_decile_avg_actual
group by
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    date_flag,
    decile_rank
  );

