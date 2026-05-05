SELECT DISTINCT
  f_e_d_m_a.benchmark_period_key,
  f_e_d_m_a.benchmark_period_name,
  f_e_d_m_a.period_start_date,
  f_e_d_m_a.period_end_date,
  f_e_d_m_a.date_flag,
  f_e_d_m_a.decile_rank,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.10, "f_e_d_m_a") }} AS p10,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.20, "f_e_d_m_a") }} AS p20,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.25, "f_e_d_m_a") }} AS p25,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.30, "f_e_d_m_a") }} AS p30,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.40, "f_e_d_m_a") }} AS p40,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.50, "f_e_d_m_a") }} AS p50,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.60, "f_e_d_m_a") }} AS p60,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.70, "f_e_d_m_a") }} AS p70,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.75, "f_e_d_m_a") }} AS p75,
  {{ calculate_percentile_by_period_flag_rank("f_e_d_m_a.avg_actual", 0.90, "f_e_d_m_a") }} AS p90,
  ROUND(
    MAX(CAST(f_e_d_m_a.avg_actual AS FLOAT64)) OVER (
      PARTITION BY
        f_e_d_m_a.benchmark_period_key,
        f_e_d_m_a.date_flag,
        f_e_d_m_a.decile_rank
    )
  ) AS max_performance
FROM
  {{ ref("int_facility_event_decile_avg_actual") }}
    AS f_e_d_m_a
