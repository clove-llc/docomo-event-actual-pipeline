SELECT
  s_f_t.facility_name,
  AVG(s_f_t.cpa) AS cpa
FROM {{ ref("stg_facility_target_cpa_master") }} AS s_f_t
GROUP BY
  s_f_t.facility_name
