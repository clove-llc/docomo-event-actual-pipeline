CREATE OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_monthly_weekday_dateflag_deviation_zscore` AS

SELECT
  f.facility_code,
  f.facility_name, # 表記ゆれしているので、マスタ側の表記に合わせる
  f_d_z.month,
  f_d_z.weekday_monthly,
  f_d_z.date_flag,
  ROUND(AVG(f_d_z.z_score), 1) AS avg_z_score
FROM `{project_id}.docomo_eventActual.facility_daily_deviation_zscore` AS f_d_z
LEFT JOIN `{project_id}.docomo_eventActual.facility_master` AS f
  ON  f_d_z.facility_code = f.facility_code
GROUP BY
  f.facility_code,
  f.facility_name,
  f_d_z.month,
  f_d_z.weekday_monthly,
  f_d_z.date_flag