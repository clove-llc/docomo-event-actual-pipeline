{#-
  BQ int_event_decile_benchmark のミラー。
  ベンチマーク期間×日付フラグ×デシル区分ごとの平均実績の分位点（p10〜p90）と最大値を算出。
  BQ は PERCENTILE_CONT(...) OVER(PARTITION BY ...) ＋ SELECT DISTINCT。
  Snowflake は窓版 PERCENTILE_CONT が無いため、PERCENTILE_CONT(p) WITHIN GROUP ＋ GROUP BY で等価に書く
  （分位点の partition = group。name/start/end は key に従属するため group に含めても同一グループ）。
-#}
select
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    date_flag,
    decile_rank,
    {{ round_bq('percentile_cont(0.10) within group (order by cast(avg_actual as float))', 0) }} as p10,
    {{ round_bq('percentile_cont(0.20) within group (order by cast(avg_actual as float))', 0) }} as p20,
    {{ round_bq('percentile_cont(0.25) within group (order by cast(avg_actual as float))', 0) }} as p25,
    {{ round_bq('percentile_cont(0.30) within group (order by cast(avg_actual as float))', 0) }} as p30,
    {{ round_bq('percentile_cont(0.40) within group (order by cast(avg_actual as float))', 0) }} as p40,
    {{ round_bq('percentile_cont(0.50) within group (order by cast(avg_actual as float))', 0) }} as p50,
    {{ round_bq('percentile_cont(0.60) within group (order by cast(avg_actual as float))', 0) }} as p60,
    {{ round_bq('percentile_cont(0.70) within group (order by cast(avg_actual as float))', 0) }} as p70,
    {{ round_bq('percentile_cont(0.75) within group (order by cast(avg_actual as float))', 0) }} as p75,
    {{ round_bq('percentile_cont(0.90) within group (order by cast(avg_actual as float))', 0) }} as p90,
    {{ round_bq('max(cast(avg_actual as float))', 0) }} as max_performance
from {{ ref('int_facility_event_decile_avg_actual') }}
group by
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    date_flag,
    decile_rank
