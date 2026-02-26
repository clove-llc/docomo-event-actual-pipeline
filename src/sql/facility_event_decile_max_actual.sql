CREATE OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_event_decile_max_actual` AS
SELECT
    f_d_a.facility_name,
    EXTRACT(MONTH FROM f_d_a.date) AS month,
    f_d_a.week_number_monthly,
    f_e_d_m.event_type,
    f_e_d_m.decile_rank,
    MAX(f_d_a.actual) AS max_actual
FROM `{project_id}.docomo_eventActual.facility_daily_actual` AS f_d_a
LEFT JOIN `{project_id}.docomo_eventActual.facility_event_decile_master` AS f_e_d_m
    ON f_d_a.facility_name = f_e_d_m.facility_name
    AND EXTRACT(MONTH FROM f_d_a.date) = f_e_d_m.month
    AND f_d_a.week_number_monthly = f_e_d_m.week_number_monthly
GROUP BY
    f_d_a.facility_name,
    month,
    f_d_a.week_number_monthly,
    f_e_d_m.event_type,
    f_e_d_m.decile_rank