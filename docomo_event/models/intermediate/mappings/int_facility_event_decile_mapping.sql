-- depends_on: {{ ref("stg_facility_master") }}
-- depends_on: {{ ref("stg_date_master_2025_2026") }}
-- depends_on: {{ ref("stg_facility_foot_traffic_sum_and_decile_by_flag") }}

SELECT DISTINCT
  f_m.facility_code,
  f_m.facility_name,
  f_m.po_level,
  f_m.regional_office,
  f_m.branch_office,
  d_m.week_number_monthly,
  d_m.date_flag,
  EXTRACT(MONTH FROM d_m.date) AS month,
  CASE
    WHEN d_m.date_flag = '正月' THEN f_f.new_year_decile_rank
    WHEN d_m.date_flag = '平日' THEN f_f.weekday_decile_rank
    WHEN d_m.date_flag = '三連休' THEN f_f.three_day_holiday_decile_rank
    WHEN d_m.date_flag = '通常土日' THEN f_f.regular_weekend_decile_rank
    WHEN d_m.date_flag = '飛び石祝日' THEN f_f.bridge_holiday_decile_rank
    WHEN d_m.date_flag = 'GW' THEN f_f.gw_decile_rank
    WHEN d_m.date_flag = 'お盆' THEN f_f.obon_decile_rank
    WHEN d_m.date_flag = '年末' THEN f_f.year_end_decile_rank
    WHEN d_m.date_flag = 'ブラックフライデー' THEN f_f.black_friday_decile_rank
  END AS decile_rank
FROM {{ ref("stg_facility_master") }} AS f_m
CROSS JOIN {{ ref("stg_date_master_2025_2026") }} AS d_m
LEFT JOIN
  {{ ref("stg_facility_foot_traffic_sum_and_decile_by_flag") }}
    AS f_f
  ON f_m.facility_code = f_f.facility_code
