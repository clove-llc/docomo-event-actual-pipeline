{#- BQ int_benchmark_periods のミラー。ベンチマーク期間の定義（固定値）。 -#}
select
    '2025_10_2025_12' as benchmark_period_key,
    '2025年10月〜2025年12月' as benchmark_period_name,
    date '2025-10-01' as period_start_date,
    date '2025-12-31' as period_end_date,
    3 as period_month_count

union all

select
    '2025_10_2026_02' as benchmark_period_key,
    '2025年10月〜2026年2月' as benchmark_period_name,
    date '2025-10-01' as period_start_date,
    date '2026-02-28' as period_end_date,
    5 as period_month_count

union all

select
    '2025_04_2026_03' as benchmark_period_key,
    '2025年4月〜2026年3月' as benchmark_period_name,
    date '2025-04-01' as period_start_date,
    date '2026-03-31' as period_end_date,
    12 as period_month_count
