WITH facility_actuals_distinct AS (
  SELECT DISTINCT -- 実績データにレコード単位の重複があるため、重複を排除してから結合する
    source_sheet_name,
    regional_office_name,
    branch_office_name,
    floor_label,
    space_name,
    area_raw,
    helper_company_name,
    staff_count_raw,
    start_date,
    end_date,
    event_date,
    actual_value,
    facility_name
  FROM {{ ref('stg_facility_actuals') }}
)
SELECT
  f_a_d.source_sheet_name,
  f_a_d.regional_office_name,
  f_a_d.branch_office_name,
  f_a_d.floor_label,
  f_a_d.space_name,
  f_a_d.area_raw,
  f_a_d.helper_company_name,
  f_a_d.staff_count_raw,
  f_a_d.start_date,
  f_a_d.end_date,
  f_a_d.event_date,
  f_a_d.actual_value,
  COALESCE(s_f_n_m.mapped_name, f_a_d.facility_name) AS facility_name
FROM facility_actuals_distinct AS f_a_d
LEFT JOIN {{ ref('stg_facility_name_mappings') }} AS s_f_n_m
  ON f_a_d.facility_name = s_f_n_m.original_name
