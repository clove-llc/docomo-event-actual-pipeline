CREATE
OR REPLACE TABLE `{project_id}.docomo_eventActual.event_decile_benchmark` AS
WITH
    decile_summary AS (
        SELECT DISTINCT
            f_e_d_m_a.month,
            f_e_d_m_a.week_number_monthly,
            f_e_d_m_a.event_type,
            f_e_d_m_a.decile_rank,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.10) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p10,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.20) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p20,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.25) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p25,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.30) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p30,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.40) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p40,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.50) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p50,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.60) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p60,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.70) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p70,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.75) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p75,
            ROUND(
                PERCENTILE_CONT(CAST(f_e_d_m_a.avg_actual AS FLOAT64), 0.90) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS p90,
            ROUND(
                MAX(CAST(f_e_d_m_a.avg_actual AS FLOAT64)) OVER (
                    PARTITION BY
                        f_e_d_m_a.month,
                        f_e_d_m_a.week_number_monthly,
                        f_e_d_m_a.event_type,
                        f_e_d_m_a.decile_rank
                )
            ) AS max_performance
        FROM
            `{project_id}.docomo_eventActual.facility_event_decile_avg_actual` AS f_e_d_m_a
    )
SELECT
    f_e_d_m.facility_name,
    f_e_d_m.po_level,
    f_e_d_m.regional_office,
    f_e_d_m.branch_office,
    f_e_d_m.month,
    f_e_d_m.week_number_monthly,
    f_e_d_m.event_type,
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
    `{project_id}.docomo_eventActual.facility_event_decile_master` AS f_e_d_m
    LEFT JOIN decile_summary AS d_s ON f_e_d_m.month = d_s.month
    AND f_e_d_m.week_number_monthly = d_s.week_number_monthly
    AND f_e_d_m.event_type = d_s.event_type
    AND f_e_d_m.decile_rank = d_s.decile_rank