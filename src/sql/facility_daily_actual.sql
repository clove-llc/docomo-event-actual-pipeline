CREATE
OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_daily_actual` AS
SELECT DISTINCT
    f_m.facility_name,
    f_m.po_level,
    f_m.regional_office,
    f_m.branch_office,
    d_m.date,
    d_m.year_month,
    d_m.week_number_monthly,
    d_m.week_number_yearly,
    d_m.weekday_name,
    d_m.weekday_holiday_with_holiday,
    d_m.date_type,
    d_m.date_flag,
    v_p.daily_result AS actual
FROM
    `{project_id}.docomo_eventActual.facility_master` AS f_m
    INNER JOIN `{project_id}.docomo_eventActual.venue_performance` AS v_p ON TRIM(f_m.facility_name) = TRIM(v_p.facility_name)
    LEFT JOIN `{project_id}.docomo_eventActual.date_master_2025_2026` AS d_m ON v_p.date = d_m.date