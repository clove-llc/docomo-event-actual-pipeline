-- depends_on: {{ ref('int_facility_daily_actual') }}
-- depends_on: {{ ref('int_facility_event_decile_mapping') }}
SELECT
  f_d_a.facility_name,
  f_d_a.po_level,
  f_d_a.regional_office,
  f_d_a.branch_office,
  f_d_a.week_number_monthly,
  f_d_a.date_flag,
  f_e_d_m.decile_rank,
  EXTRACT(
    MONTH
    FROM
    f_d_a.date
  ) AS month,
  ROUND(AVG(f_d_a.actual)) AS avg_actual
FROM
  {{ ref("int_facility_daily_actual") }} AS f_d_a
LEFT JOIN
  {{ ref("int_facility_event_decile_mapping") }} AS f_e_d_m
  ON
    f_d_a.facility_name = f_e_d_m.facility_name
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
