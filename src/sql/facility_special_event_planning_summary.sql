CREATE OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_special_event_planning_summary` AS

WITH stats_summary AS (
    SELECT
        f_d_a.facility_name,
        -- 施設ごとの直近実績（日付が最大の実績を抽出）
        MAX_BY(f_d_a.actual, f_d_a.date) AS latest_actual
    FROM `{project_id}.docomo_eventActual.facility_daily_actual` AS f_d_a
    GROUP BY
        f_d_a.facility_name
), base AS (
    SELECT
        e_d_b.facility_name,
        e_d_b.po_level,
        e_d_b.branch_office,
        e_d_b.event_type,
        ROUND(AVG(f_e_d_m_a.max_actual)) AS daily_actual,
        ROUND(AVG(s_s.latest_actual)) AS latest_actual,
        ROUND(AVG(e_d_b.decile_rank)) AS decile_rank,
        ROUND(AVG(e_d_b.p25)) AS p25, -- 実績下位25%の実績値
        ROUND(AVG(e_d_b.p50)) AS p50, -- デシル区分の中央値
        ROUND(AVG(e_d_b.p60)) AS p60, -- 実績上位40%の実績値
        ROUND(AVG(e_d_b.p70)) AS p70, -- 実績上位30%の実績値
        ROUND(AVG(e_d_b.p75)) AS p75, -- 実績上位25%の実績値
        ROUND(AVG(e_d_b.p90)) AS p90, -- 実績上位10%の実績値
        ROUND(AVG(e_d_b.max_performance)) AS max_performance, -- デシル区分の最大の実績値
    FROM `{project_id}.docomo_eventActual.event_decile_benchmark` AS e_d_b
    LEFT JOIN `{project_id}.docomo_eventActual.facility_event_decile_max_actual` AS f_e_d_m_a
        ON e_d_b.facility_name = f_e_d_m_a.facility_name
        AND e_d_b.month = f_e_d_m_a.month
        AND e_d_b.week_number_monthly = f_e_d_m_a.week_number_monthly
        AND e_d_b.event_type = f_e_d_m_a.event_type
        AND e_d_b.decile_rank = f_e_d_m_a.decile_rank
    LEFT JOIN stats_summary AS s_s
        ON e_d_b.facility_name = s_s.facility_name
    WHERE e_d_b.event_type IN ('正月', '年末', 'GW', 'お盆', 'ブラックフライデー')
    GROUP BY
        e_d_b.facility_name,
        e_d_b.po_level,
        e_d_b.branch_office,
        e_d_b.event_type
), challenge_standard_summary AS (
    SELECT
        *,
        CASE
            WHEN daily_actual IS NULL OR daily_actual < p50 THEN p50
            WHEN daily_actual >= max_performance THEN max_performance
            WHEN daily_actual < p50 THEN p50
            WHEN daily_actual < p60 THEN p60
            WHEN daily_actual < p70 THEN p70
            WHEN daily_actual < p75 THEN p75
            WHEN daily_actual < p90 THEN p90
            ELSE max_performance
        END AS standard_target -- 標準目標
    FROM base
)
SELECT
    *,
    CASE
        WHEN standard_target >= max_performance THEN max_performance
        WHEN standard_target < p60 THEN p60
        WHEN standard_target < p70 THEN p70
        WHEN standard_target < p75 THEN p75
        WHEN standard_target < p90 THEN p90
        ELSE max_performance
    END AS challenge_target
FROM challenge_standard_summary