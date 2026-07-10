SELECT DISTINCT
  f.facility_code,
  f.facility_name,
  f.month,
  f.date_flag,
  ROUND(AVG(CAST(f.avg_z_score AS NUMERIC)), 1) AS avg_z_score
FROM {{ ref("int_facility_monthly_weekday_dateflag_deviation_zscore") }} AS f
GROUP BY
  f.facility_code,
  f.facility_name,
  f.month,
  f.date_flag
