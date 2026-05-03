-- depends_on: {{ ref('stg_facility_master') }}
-- depends_on: {{ ref('stg_date_master_2025_2026') }}
-- depends_on: {{ ref('stg_venue_performance') }}
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
  {{ ref("stg_facility_master") }} AS f_m
INNER JOIN
  {{ ref("stg_venue_performance") }} AS v_p
  ON f_m.facility_name = v_p.facility_name
LEFT JOIN {{ ref("stg_date_master_2025_2026") }} AS d_m ON v_p.date = d_m.date
