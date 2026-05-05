WITH base AS (
  SELECT
    p.benchmark_period_key,
    p.benchmark_period_name,
    p.period_start_date,
    p.period_end_date,
    s_f_m.facility_code,
    s_f_m.facility_name,
    s_f_m.po_level,
    s_f_m.regional_office,
    s_f_m.branch_office,
    s_d_m.date,
    s_d_m.week_number_monthly,
    s_d_m.date_flag
  FROM {{ ref("stg_facility_master") }} AS s_f_m
  CROSS JOIN {{ ref("stg_date_master_2026_2027") }} AS s_d_m
  CROSS JOIN {{ ref("int_benchmark_periods") }} AS p
)

SELECT
  b.benchmark_period_key,
  b.benchmark_period_name,
  b.period_start_date,
  b.period_end_date,
  b.facility_code,
  b.facility_name,
  b.po_level,
  b.regional_office,
  b.branch_office,
  b.date,
  b.week_number_monthly,
  b.date_flag,
  f_e_p_s.standard_target,
  f_e_p_s.challenge_target,
  f_e_p_s.p50,
  EXTRACT(MONTH FROM b.date) AS month,
  ROUND(f_e_p_s.standard_target * COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  )) AS standard_target_seasonal,
  ROUND(f_e_p_s.challenge_target * COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  )) AS challenge_target_seasonal,
  ROUND(f_e_p_s.p50 * COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  )) AS p50_seasonal
FROM base AS b
LEFT JOIN {{ ref("int_facility_event_planning_snapshot") }} AS f_e_p_s
  ON
    b.benchmark_period_key = f_e_p_s.benchmark_period_key
    AND b.facility_code = f_e_p_s.facility_code
    AND b.date_flag = f_e_p_s.date_flag
-- 施設 × 月番号 × 週番号 × 日付フラグの粒度で結合
LEFT JOIN {{ ref("int_facility_monthly_weekday_dateflag_deviation_zscore") }} AS i_f_m_w_d_z
  ON
    b.facility_code = i_f_m_w_d_z.facility_code
    AND EXTRACT(MONTH FROM b.date) = i_f_m_w_d_z.month
    AND b.week_number_monthly = i_f_m_w_d_z.weekday_monthly
    AND b.date_flag = i_f_m_w_d_z.date_flag
-- 2026年と2024年では週番号が異なるかもしれないので、施設 × 月番号 × 日付フラグの粒度で結合
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS i_f_m_d_z
  ON
    b.facility_code = i_f_m_d_z.facility_code
    AND EXTRACT(MONTH FROM b.date) = i_f_m_d_z.month
    AND b.date_flag = i_f_m_d_z.date_flag
-- 施設 × 月 × 三連休
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS i_f_m_3h
  ON
    b.facility_code = i_f_m_3h.facility_code
    AND EXTRACT(MONTH FROM b.date) = i_f_m_3h.month
    AND i_f_m_3h.date_flag = '三連休'
-- 施設 × 月 × 通常土日
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS i_f_m_d_g_z
  ON
    b.facility_code = i_f_m_d_g_z.facility_code
    AND EXTRACT(MONTH FROM b.date) = i_f_m_d_g_z.month
    AND i_f_m_d_g_z.date_flag = '通常土日'
