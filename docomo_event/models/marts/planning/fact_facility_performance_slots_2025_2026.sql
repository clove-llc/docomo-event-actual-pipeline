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
    s_d_m.date_flag,
    EXTRACT(MONTH FROM s_d_m.date) AS month
  FROM {{ ref("stg_facility_master") }} AS s_f_m
  CROSS JOIN {{ ref("stg_date_master_2025_2026") }} AS s_d_m
  CROSS JOIN {{ ref("int_benchmark_periods") }} AS p
  WHERE p.benchmark_period_key = '2025_10_2026_02'
),

base_monthly_week_dateflag AS (
  SELECT DISTINCT
    b.benchmark_period_key,
    b.benchmark_period_name,
    b.period_start_date,
    b.period_end_date,
    b.facility_code,
    b.facility_name,
    b.po_level,
    b.regional_office,
    b.branch_office,
    b.month,
    b.week_number_monthly,
    b.date_flag
  FROM base AS b
),

planning_snapshot_all_period AS (
  SELECT
    facility_code,
    date_flag,
    decile_rank,
    avg_actual,
    p25,
    p60,
    p70,
    p75,
    p90,
    max_performance,
    standard_target AS all_period_standard_target,
    challenge_target AS all_period_challenge_target,
    p50 AS all_period_p50
  FROM {{ ref("int_facility_event_planning_snapshot") }}
  WHERE benchmark_period_key = '2025_04_2026_03'
)


SELECT
  b_m_w_d.benchmark_period_key,
  b_m_w_d.benchmark_period_name,
  b_m_w_d.period_start_date,
  b_m_w_d.period_end_date,
  b_m_w_d.facility_code,
  b_m_w_d.facility_name,
  b_m_w_d.po_level,
  b_m_w_d.regional_office,
  b_m_w_d.branch_office,
  b_m_w_d.month,
  b_m_w_d.week_number_monthly,
  b_m_w_d.date_flag,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.decile_rank
    ELSE f_e_p_s.decile_rank
  END AS decile_rank,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.avg_actual
    ELSE f_e_p_s.avg_actual
  END AS avg_actual,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.p25
    ELSE f_e_p_s.p25
  END AS p25,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.p60
    ELSE f_e_p_s.p60
  END AS p60,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.p70
    ELSE f_e_p_s.p70
  END AS p70,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.p75
    ELSE f_e_p_s.p75
  END AS p75,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.p90
    ELSE f_e_p_s.p90
  END AS p90,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.max_performance
    ELSE f_e_p_s.max_performance
  END AS max_performance,
  COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  ) AS avg_z_score,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.all_period_standard_target
    ELSE f_e_p_s.standard_target
  END AS standard_target,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.all_period_challenge_target
    ELSE f_e_p_s.challenge_target
  END AS challenge_target,
  CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.all_period_p50
    ELSE f_e_p_s.p50
  END AS p50,
  ROUND(CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.all_period_standard_target
    ELSE f_e_p_s.standard_target
  END * COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  )) AS standard_target_seasonal,
  ROUND(CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.all_period_challenge_target
    ELSE f_e_p_s.challenge_target
  END * COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  )) AS challenge_target_seasonal,
  ROUND(CASE
    WHEN b_m_w_d.date_flag = 'GW' OR b_m_w_d.date_flag = 'お盆' THEN f_e_p_s_all_period.all_period_p50
    ELSE f_e_p_s.p50
  END * COALESCE(
    i_f_m_w_d_z.avg_z_score,
    i_f_m_d_z.avg_z_score,
    i_f_m_3h.avg_z_score,
    i_f_m_d_g_z.avg_z_score
  )) AS p50_seasonal
FROM base_monthly_week_dateflag AS b_m_w_d
LEFT JOIN {{ ref("int_facility_event_planning_snapshot") }} AS f_e_p_s
  ON
    b_m_w_d.benchmark_period_key = f_e_p_s.benchmark_period_key
    AND b_m_w_d.facility_code = f_e_p_s.facility_code
    AND b_m_w_d.date_flag = f_e_p_s.date_flag
LEFT JOIN planning_snapshot_all_period AS f_e_p_s_all_period
  ON
    b_m_w_d.facility_code = f_e_p_s_all_period.facility_code
    AND b_m_w_d.date_flag = f_e_p_s_all_period.date_flag
LEFT JOIN {{ ref("int_facility_monthly_weekday_dateflag_deviation_zscore") }} AS i_f_m_w_d_z
  ON
    b_m_w_d.facility_code = i_f_m_w_d_z.facility_code
    AND b_m_w_d.month = i_f_m_w_d_z.month
    AND b_m_w_d.week_number_monthly = i_f_m_w_d_z.weekday_monthly
    AND b_m_w_d.date_flag = i_f_m_w_d_z.date_flag
-- 2026年と2024年では週番号が異なるかもしれないので、施設 × 月番号 × 日付フラグの粒度で結合
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS i_f_m_d_z
  ON
    b_m_w_d.facility_code = i_f_m_d_z.facility_code
    AND b_m_w_d.month = i_f_m_d_z.month
    AND b_m_w_d.date_flag = i_f_m_d_z.date_flag
-- 施設 × 月 × 三連休
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS i_f_m_3h
  ON
    b_m_w_d.facility_code = i_f_m_3h.facility_code
    AND b_m_w_d.month = i_f_m_3h.month
    AND i_f_m_3h.date_flag = '三連休'
-- 施設 × 月 × 通常土日
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS i_f_m_d_g_z
  ON
    b_m_w_d.facility_code = i_f_m_d_g_z.facility_code
    AND b_m_w_d.month = i_f_m_d_g_z.month
    AND i_f_m_d_g_z.date_flag = '通常土日'
