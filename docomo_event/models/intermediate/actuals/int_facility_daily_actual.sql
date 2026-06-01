SELECT DISTINCT
  f_m.facility_code,
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
  f_a.actual_value AS actual
FROM
  {{ ref("stg_facility_master") }} AS f_m
INNER JOIN
  {{ ref("int_facility_actuals") }} AS f_a
  ON f_m.facility_name = f_a.facility_name
LEFT JOIN {{ ref("stg_date_master") }} AS d_m ON f_a.event_date = d_m.date
