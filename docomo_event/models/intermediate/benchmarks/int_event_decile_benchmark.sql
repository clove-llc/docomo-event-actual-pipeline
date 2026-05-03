-- depends_on: {{ ref('int_facility_event_decile_avg_actual') }}
-- depends_on: {{ ref('int_facility_event_decile_mapping') }}
WITH decile_summary AS (
  SELECT DISTINCT
    f_e_d_m_a.month,
    f_e_d_m_a.week_number_monthly,
    f_e_d_m_a.date_flag,
    f_e_d_m_a.decile_rank,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.10, "f_e_d_m_a") }} AS p10,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.20, "f_e_d_m_a") }} AS p20,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.25, "f_e_d_m_a") }} AS p25,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.30, "f_e_d_m_a") }} AS p30,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.40, "f_e_d_m_a") }} AS p40,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.50, "f_e_d_m_a") }} AS p50,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.60, "f_e_d_m_a") }} AS p60,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.70, "f_e_d_m_a") }} AS p70,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.75, "f_e_d_m_a") }} AS p75,
    {{ calculate_percentile_by_month_week_flag_rank("f_e_d_m_a.avg_actual", 0.90, "f_e_d_m_a") }} AS p90,
    ROUND(
      MAX(CAST(f_e_d_m_a.avg_actual AS FLOAT64)) OVER (
        PARTITION BY
          f_e_d_m_a.month,
          f_e_d_m_a.week_number_monthly,
          f_e_d_m_a.date_flag,
          f_e_d_m_a.decile_rank
      )
    ) AS max_performance
  FROM
    {{ ref("int_facility_event_decile_avg_actual") }}
      AS f_e_d_m_a
)

SELECT
  f_e_d_m.facility_name,
  f_e_d_m.po_level,
  f_e_d_m.regional_office,
  f_e_d_m.branch_office,
  f_e_d_m.month,
  f_e_d_m.week_number_monthly,
  f_e_d_m.date_flag,
  f_e_d_m.decile_rank,
  d_s.p10,
  d_s.p20,
  d_s.p25,
  d_s.p30,
  d_s.p40,
  d_s.p50,
  d_s.p60,
  d_s.p70,
  d_s.p75,
  d_s.p90,
  d_s.max_performance
FROM
  {{ ref("int_facility_event_decile_mapping") }} AS f_e_d_m
LEFT JOIN decile_summary
  AS d_s ON f_e_d_m.month = d_s.month
AND f_e_d_m.week_number_monthly = d_s.week_number_monthly
AND f_e_d_m.date_flag = d_s.date_flag
AND f_e_d_m.decile_rank = d_s.decile_rank
