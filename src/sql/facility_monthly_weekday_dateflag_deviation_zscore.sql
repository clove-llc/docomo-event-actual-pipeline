CREATE OR REPLACE TABLE `digital-well-456700-i9.docomo_eventActual.facility_monthly_weekday_dateflag_deviation_zscore` AS

SELECT
  f.no,
  TRIM(f.display_facility_name) AS display_facility_name, # 表記ゆれしているので、マスタ側の表記に合わせる
  f_d_z.month,
  f_d_z.weekday_monthly,
  f_d_z.date_flag,
  ROUND(AVG(f_d_z.z_score), 1) AS avg_z_score
FROM `digital-well-456700-i9.docomo_eventActual.facility_daily_deviation_zscore` AS f_d_z
LEFT JOIN `digital-well-456700-i9.docomo_eventActual.facility_master` AS f
  ON  f_d_z.facility_code = f.no
GROUP BY
  f.`no`,
  f.display_facility_name,
  f_d_z.month,
  f_d_z.weekday_monthly,
  f_d_z.date_flag