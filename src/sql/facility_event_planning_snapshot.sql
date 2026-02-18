CREATE OR REPLACE TABLE `digital-well-456700-i9.docomo_eventActual.facility_event_planning_snapshot` AS

WITH stats_summary AS (
    SELECT
        f_d_a.facility_name,
        -- 施設ごとの直近実績（日付が最大の実績を抽出）
        MAX_BY(f_d_a.actual, f_d_a.date) AS latest_actual
    FROM `digital-well-456700-i9.docomo_eventActual.facility_daily_actual` AS f_d_a
    GROUP BY
        f_d_a.facility_name
), base AS (
    SELECT
        e_d_b.facility_name,
        e_d_b.po_level,
        e_d_b.branch_office,
        e_d_b.month,
        e_d_b.week_number_monthly,
        e_d_b.event_type,
        f_e_d_m_a.max_actual AS daily_actual,
        s_s.latest_actual,
        e_d_b.decile_rank,
        e_d_b.p25, -- 実績下位25%の実績値
        e_d_b.p50, -- デシル区分の中央値
        e_d_b.p60, -- 実績上位40%の実績値
        e_d_b.p70, -- 実績上位30%の実績値
        e_d_b.p75, -- 実績上位25%の実績値
        e_d_b.p90, -- 実績上位10%の実績値
        e_d_b.max_performance, -- デシル区分の最大の実績値
        CASE
            WHEN f_e_d_m_a.max_actual IS NULL OR f_e_d_m_a.max_actual < e_d_b.p50 THEN e_d_b.p50
            WHEN f_e_d_m_a.max_actual >= e_d_b.max_performance THEN e_d_b.max_performance
            WHEN f_e_d_m_a.max_actual < e_d_b.p50 THEN e_d_b.p50
            WHEN f_e_d_m_a.max_actual < e_d_b.p60 THEN e_d_b.p60
            WHEN f_e_d_m_a.max_actual < e_d_b.p70 THEN e_d_b.p70
            WHEN f_e_d_m_a.max_actual < e_d_b.p75 THEN e_d_b.p75
            WHEN f_e_d_m_a.max_actual < e_d_b.p90 THEN e_d_b.p90
            ELSE e_d_b.max_performance
        END AS standard_target -- 標準目標
    FROM `digital-well-456700-i9.docomo_eventActual.event_decile_benchmark` AS e_d_b
    LEFT JOIN `digital-well-456700-i9.docomo_eventActual.facility_event_decile_max_actual` AS f_e_d_m_a
        ON e_d_b.facility_name = f_e_d_m_a.facility_name
        AND e_d_b.month = f_e_d_m_a.month
        AND e_d_b.week_number_monthly = f_e_d_m_a.week_number_monthly
        AND e_d_b.event_type = f_e_d_m_a.event_type
        AND e_d_b.decile_rank = f_e_d_m_a.decile_rank
    LEFT JOIN stats_summary AS s_s
        ON e_d_b.facility_name = s_s.facility_name
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
FROM base;
