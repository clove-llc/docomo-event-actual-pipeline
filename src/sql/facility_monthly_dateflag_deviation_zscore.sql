CREATE OR REPLACE TABLE `{project_id}.docomo_eventActual.facility_monthly_dateflag_deviation_zscore` AS

SELECT DISTINCT
  f.no,
  TRIM(f.display_facility_name) AS display_facility_name, # 表記ゆれしているので、マスタ側の表記に合わせる
  f.month,
  f.date_flag,
  ROUND(AVG(avg_z_score), 1) AS avg_z_score
FROM `{project_id}.docomo_eventActual.facility_monthly_weekday_dateflag_deviation_zscore` AS f
GROUP BY
  f.`no`,
  f.display_facility_name,
  f.month,
  f.date_flag