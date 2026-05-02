CREATE
OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_event_decile_avg_actual` AS
SELECT
    f_d_a.facility_name,
    f_d_a.po_level,
    f_d_a.regional_office,
    f_d_a.branch_office,
    EXTRACT(
        MONTH
        FROM
            f_d_a.date
    ) AS month,
    f_d_a.week_number_monthly,
    f_d_a.date_flag,
    f_e_d_m.decile_rank,
    ROUND(AVG(f_d_a.actual)) AS avg_actual
FROM
    `{project_id}.docomo_eventActual.facility_daily_actual` AS f_d_a
    LEFT JOIN `{project_id}.docomo_eventActual.facility_event_decile_master` AS f_e_d_m ON f_d_a.facility_name = f_e_d_m.facility_name
    AND EXTRACT(
        MONTH
        FROM
            f_d_a.date
    ) = f_e_d_m.month
    AND f_d_a.week_number_monthly = f_e_d_m.week_number_monthly
    AND f_d_a.date_flag = f_e_d_m.date_flag
GROUP BY
    f_d_a.facility_name,
    f_d_a.po_level,
    f_d_a.regional_office,
    f_d_a.branch_office,
    month,
    f_d_a.week_number_monthly,
    f_d_a.date_flag,
    f_e_d_m.decile_rank