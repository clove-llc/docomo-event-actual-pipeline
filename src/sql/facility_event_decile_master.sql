CREATE OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_event_decile_master` AS

SELECT DISTINCT
  f_m.no,
  TRIM(f_m.display_facility_name, ' ') AS facility_name,
  f_m.po_level,
  f_m.regional_office,
  f_m.branch_office,
  EXTRACT(MONTH FROM d_m.date) AS month,
  d_m.week_number_monthly,
  d_m.event_type,
  CASE
    WHEN d_m.event_type = '正月' THEN f_f.new_year_decile_rank
    WHEN d_m.event_type = '平日' THEN f_f.weekday_decile_rank
    WHEN d_m.event_type = '三連休' THEN f_f.three_day_holiday_decile_rank
    WHEN d_m.event_type = '通常土日' THEN f_f.regular_weekend_decile_rank
    WHEN d_m.event_type = '飛び石祝日' THEN f_f.bridge_holiday_decile_rank
    WHEN d_m.event_type = 'GW' THEN f_f.gw_decile_rank
    WHEN d_m.event_type = 'お盆' THEN f_f.obon_decile_rank
    WHEN d_m.event_type = '年末' THEN f_f.year_end_decile_rank
    WHEN d_m.event_type = 'ブラックフライデー' THEN f_f.black_friday_decile_rank
    ELSE NULL
  END AS decile_rank
FROM `{project_id}.docomo_eventActual.facility_master` AS f_m
CROSS JOIN `{project_id}.docomo_eventActual.date_master_2025_2026` AS d_m
LEFT JOIN `{project_id}.docomo_eventActual.facility_foot_traffic_sum_and_decile_by_flag` AS f_f
  ON f_m.no = f_f.facility_code