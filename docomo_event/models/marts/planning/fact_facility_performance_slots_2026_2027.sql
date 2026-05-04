-- depends_on: {{ ref("int_facility_event_planning_snapshot") }}
-- depends_on: {{ ref("stg_facility_master") }}
-- depends_on: {{ ref("stg_date_master_2026_2027") }}
-- depends_on: {{ ref("int_facility_monthly_weekday_dateflag_deviation_zscore") }}
-- depends_on: {{ ref("int_facility_monthly_dateflag_deviation_zscore") }}

WITH facility_event_planning_snapshot_monthly AS (
  SELECT
    f_e_p_s.month,
    f_e_p_s.date_flag,
    TRIM(f_e_p_s.facility_name) AS facility_name,
    ROUND(AVG(f_e_p_s.standard_target)) AS avg_standard_target,
    ROUND(AVG(f_e_p_s.challenge_target)) AS avg_challenge_target,
    ROUND(AVG(f_e_p_s.p50)) AS avg_p50
  FROM {{ ref("int_facility_event_planning_snapshot") }} AS f_e_p_s
  GROUP BY
    f_e_p_s.facility_name,
    f_e_p_s.month,
    f_e_p_s.date_flag
),

base AS (
  SELECT
    s_f_m.*,
    s_d_m.*
  FROM {{ ref("stg_facility_master") }} AS s_f_m
  CROSS JOIN {{ ref("stg_date_master_2026_2027") }} AS s_d_m
)

SELECT
  b.facility_name,
  b.po_level,
  b.regional_office,
  b.branch_office,
  b.date,
  b.week_number_monthly,
  b.date_flag,
  EXTRACT(MONTH FROM b.date) AS month,
  COALESCE(f_e_p_s.standard_target, f_e_p_s_m.avg_standard_target) AS standard_target,
  COALESCE(f_e_p_s.challenge_target, f_e_p_s_m.avg_challenge_target) AS challenge_target,
  COALESCE(f_e_p_s.p50, f_e_p_s_m.avg_p50) AS p50,
  ROUND(COALESCE(f_e_p_s.standard_target, f_e_p_s_m.avg_standard_target) * COALESCE(
    f_m.avg_z_score,
    f_m_m.avg_z_score,
    f_m_3h.avg_z_score,
    f_m_we.avg_z_score
  )) AS standard_target_seasonal,
  ROUND(COALESCE(f_e_p_s.challenge_target, f_e_p_s_m.avg_challenge_target) * COALESCE(
    f_m.avg_z_score,
    f_m_m.avg_z_score,
    f_m_3h.avg_z_score,
    f_m_we.avg_z_score
  )) AS challenge_target_seasonal,
  ROUND(COALESCE(f_e_p_s.p50, f_e_p_s_m.avg_p50) * COALESCE(
    f_m.avg_z_score,
    f_m_m.avg_z_score,
    f_m_3h.avg_z_score,
    f_m_we.avg_z_score
  )) AS p50_seasonal
FROM base AS b
LEFT JOIN {{ ref("int_facility_event_planning_snapshot") }} AS f_e_p_s
  ON
    b.facility_name = f_e_p_s.facility_name
    AND EXTRACT(MONTH FROM b.date) = f_e_p_s.month
    AND b.week_number_monthly = f_e_p_s.week_number_monthly
    AND b.date_flag = f_e_p_s.date_flag
LEFT JOIN facility_event_planning_snapshot_monthly AS f_e_p_s_m
  ON
    b.facility_name = f_e_p_s_m.facility_name
    AND EXTRACT(MONTH FROM b.date) = f_e_p_s_m.month
    AND b.date_flag = f_e_p_s_m.date_flag
-- 施設 × 月番号 × 週番号 × 日付フラグの粒度で結合
LEFT JOIN {{ ref("int_facility_monthly_weekday_dateflag_deviation_zscore") }} AS f_m
  ON
    b.facility_name = f_m.facility_name
    AND EXTRACT(MONTH FROM b.date) = f_m.month
    AND b.week_number_monthly = f_m.weekday_monthly
    AND b.date_flag = f_m.date_flag
-- 2026年と2024年では週番号が異なるかもしれないので、施設 × 月番号 × 日付フラグの粒度で結合
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS f_m_m
  ON
    b.facility_name = f_m_m.facility_name
    AND EXTRACT(MONTH FROM b.date) = f_m_m.month
    AND b.date_flag = f_m_m.date_flag
-- 施設 × 月 × 三連休
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS f_m_3h
  ON
    b.facility_name = f_m_3h.facility_name
    AND EXTRACT(MONTH FROM b.date) = f_m_3h.month
    AND f_m_3h.date_flag = '三連休'
-- 施設 × 月 × 通常土日
LEFT JOIN {{ ref("int_facility_monthly_dateflag_deviation_zscore") }} AS f_m_we
  ON
    b.facility_name = f_m_we.facility_name
    AND EXTRACT(MONTH FROM b.date) = f_m_we.month
    AND f_m_we.date_flag = '通常土日'
