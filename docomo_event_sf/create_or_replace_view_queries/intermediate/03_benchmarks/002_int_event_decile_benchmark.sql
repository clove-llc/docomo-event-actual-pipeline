
  create or replace   view HARATO.INT.int_event_decile_benchmark
  
  
  
  
  as (
    select
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    date_flag,
    decile_rank,
    round(cast((percentile_cont(0.10) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p10,
    round(cast((percentile_cont(0.20) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p20,
    round(cast((percentile_cont(0.25) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p25,
    round(cast((percentile_cont(0.30) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p30,
    round(cast((percentile_cont(0.40) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p40,
    round(cast((percentile_cont(0.50) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p50,
    round(cast((percentile_cont(0.60) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p60,
    round(cast((percentile_cont(0.70) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p70,
    round(cast((percentile_cont(0.75) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p75,
    round(cast((percentile_cont(0.90) within group (order by cast(avg_actual as float))) as number(38, 18)), 0) as p90,
    round(cast((max(cast(avg_actual as float))) as number(38, 18)), 0) as max_performance
from HARATO.INT.int_facility_event_decile_avg_actual
group by
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    date_flag,
    decile_rank
  );

