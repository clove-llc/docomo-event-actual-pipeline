WITH joined AS (
  SELECT
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
  FROM {{ ref("int_facility_daily_actual") }} AS d
  INNER JOIN {{ ref("int_benchmark_periods") }} AS p
    ON d.date BETWEEN p.period_start_date AND p.period_end_date
  LEFT JOIN {{ ref("int_facility_event_decile_mapping") }} AS m
    ON
      d.facility_code = m.facility_code
      AND d.date_flag = m.date_flag
)

SELECT
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
  COUNT(*) AS actual_days,
  SUM(actual) AS total_actual,
  ROUND(AVG(actual)) AS avg_actual
FROM joined
GROUP BY
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
