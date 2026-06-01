SELECT
  s_f_a.source_sheet_name,
  s_f_a.regional_office_name,
  s_f_a.branch_office_name,
  s_f_a.floor_label,
  s_f_a.space_name,
  s_f_a.area_raw,
  s_f_a.helper_company_name,
  s_f_a.staff_count_raw,
  s_f_a.start_date,
  s_f_a.end_date,
  s_f_a.event_date,
  s_f_a.actual_value,
  COALESCE(s_f_n_m.mapped_name, s_f_a.facility_name) AS facility_name
FROM {{ ref('stg_facility_actuals') }} AS s_f_a
LEFT JOIN {{ ref('stg_facility_name_mappings') }} AS s_f_n_m
  ON s_f_a.facility_name = s_f_n_m.original_name
