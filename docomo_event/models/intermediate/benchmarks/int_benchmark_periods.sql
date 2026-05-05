SELECT
  '2025_10_2025_12' AS benchmark_period_key,
  '2025年10月〜2025年12月' AS benchmark_period_name,
  DATE '2025-10-01' AS period_start_date,
  DATE '2025-12-31' AS period_end_date,
  3 AS period_month_count

UNION ALL

SELECT
  '2025_10_2026_02' AS benchmark_period_key,
  '2025年10月〜2026年2月' AS benchmark_period_name,
  DATE '2025-10-01' AS period_start_date,
  DATE '2026-02-28' AS period_end_date,
  5 AS period_month_count

UNION ALL

SELECT
  '2025_04_2026_03' AS benchmark_period_key,
  '2025年4月〜2026年3月' AS benchmark_period_name,
  DATE '2025-04-01' AS period_start_date,
  DATE '2026-03-31' AS period_end_date,
  12 AS period_month_count
