SELECT
  f.facility_code,
  f.facility_name,
  f_d_z.month,
  f_d_z.week_number_monthly,
  f_d_z.date_flag,
  ROUND(AVG(CAST(f_d_z.z_score AS NUMERIC)), 1) AS avg_z_score
FROM {{ ref("stg_facility_daily_deviation_zscore") }} AS f_d_z
LEFT JOIN {{ ref("stg_facility_master") }} AS f
  ON f_d_z.facility_code = f.facility_code
GROUP BY
  f.facility_code,
  f.facility_name,
  f_d_z.month,
  f_d_z.week_number_monthly,
  f_d_z.date_flag
