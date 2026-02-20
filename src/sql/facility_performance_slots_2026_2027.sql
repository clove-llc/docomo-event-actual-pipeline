CREATE OR REPLACE TABLE `docomo_event_actual_2026.facility_performance_slots_2026_2027` AS

WITH facility_event_planning_snapshot_monthly AS (
    SELECT
        TRIM(f_e_p_s.facility_name) AS facility_name,
        f_e_p_s.month,
        f_e_p_s.event_type,
        ROUND(AVG(f_e_p_s.standard_target)) AS avg_standard_target,
        ROUND(AVG(f_e_p_s.challenge_target)) AS avg_challenge_target,
        ROUND(AVG(f_e_p_s.p50)) AS avg_p50,
FROM `docomo_eventActual.facility_event_planning_snapshot` AS f_e_p_s
GROUP BY
    f_e_p_s.facility_name,
    f_e_p_s.month,
    f_e_p_s.event_type
), base AS (
    SELECT
        *
    FROM `docomo_eventActual.facility_master` AS f
    CROSS JOIN `docomo_eventActual.date_master_2026_2027` AS d
)

SELECT
    TRIM(b.display_facility_name) AS display_facility_name,
    b.po_level,
    b.regional_office,
    b.branch_office,
    b.date,
    EXTRACT(MONTH FROM b.date) AS month,
    b.week_number_monthly,
    b.event_type,
    COALESCE(f_e_p_s.standard_target, f_e_p_s_m.avg_standard_target) AS standard_target,
    COALESCE(f_e_p_s.challenge_target, f_e_p_s_m.avg_challenge_target) AS challenge_target,
    COALESCE(f_e_p_s.p50, f_e_p_s_m.avg_p50) AS p50,
    ROUND(COALESCE(f_e_p_s.standard_target, f_e_p_s_m.avg_standard_target) * COALESCE(
        f_m.avg_z_score,
        f_m_m.avg_z_score,
        f_m_3h.avg_z_score,
        f_m_we.avg_z_score)) AS standard_target_seasonal,
    ROUND(COALESCE(f_e_p_s.challenge_target, f_e_p_s_m.avg_challenge_target) * COALESCE(
        f_m.avg_z_score,
        f_m_m.avg_z_score,
        f_m_3h.avg_z_score,
        f_m_we.avg_z_score)) AS challenge_target_seasonal,
    ROUND(COALESCE(f_e_p_s.p50, f_e_p_s_m.avg_p50) * COALESCE(
        f_m.avg_z_score,
        f_m_m.avg_z_score,
        f_m_3h.avg_z_score,
        f_m_we.avg_z_score)) AS p50_seasonal
FROM base AS b
LEFT JOIN `docomo_eventActual.facility_event_planning_snapshot` AS f_e_p_s
    ON
        TRIM(b.display_facility_name) = TRIM(f_e_p_s.facility_name)
        AND EXTRACT(MONTH FROM b.date) = f_e_p_s.month
        AND b.week_number_monthly = f_e_p_s.week_number_monthly
        AND b.event_type = f_e_p_s.event_type
LEFT JOIN facility_event_planning_snapshot_monthly AS f_e_p_s_m
    ON
        TRIM(b.display_facility_name) = f_e_p_s_m.facility_name
        AND EXTRACT(MONTH FROM b.date) = f_e_p_s_m.month
        AND b.event_type = f_e_p_s_m.event_type
-- 施設 × 月番号 × 週番号 × 日付フラグの粒度で結合
LEFT JOIN `docomo_eventActual.facility_monthly_weekday_dateflag_deviation_zscore` AS f_m
    ON
        TRIM(b.display_facility_name) = TRIM(f_m.display_facility_name)
        AND EXTRACT(MONTH FROM b.date) = f_m.month
        AND b.week_number_monthly = f_m.weekday_monthly
        AND b.event_type = f_m.date_flag
-- 2026年と2024年では週番号が異なるかもしれないので、施設 × 月番号 × 日付フラグの粒度で結合
LEFT JOIN `docomo_eventActual.facility_monthly_dateflag_deviation_zscore` AS f_m_m
    ON
        TRIM(b.display_facility_name) = TRIM(f_m_m.display_facility_name)
        AND EXTRACT(MONTH FROM b.date) = f_m_m.month
        AND b.event_type = f_m_m.date_flag
-- 施設 × 月 × 三連休
LEFT JOIN `docomo_eventActual.facility_monthly_dateflag_deviation_zscore` AS f_m_3h
    ON
        TRIM(b.display_facility_name) = TRIM(f_m_3h.display_facility_name)
        AND EXTRACT(MONTH FROM b.date) = f_m_3h.month
        AND f_m_3h.date_flag = '三連休'
-- 施設 × 月 × 通常土日
LEFT JOIN `docomo_eventActual.facility_monthly_dateflag_deviation_zscore` AS f_m_we
    ON
        TRIM(b.display_facility_name) = TRIM(f_m_we.display_facility_name)
        AND EXTRACT(MONTH FROM b.date) = f_m_we.month
        AND f_m_we.date_flag = '通常土日'