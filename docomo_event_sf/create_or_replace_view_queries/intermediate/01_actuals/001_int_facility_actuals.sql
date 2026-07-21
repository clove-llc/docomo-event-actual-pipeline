
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.int_facility_actuals
  
  
  
  
  as (
    with facility_actuals_distinct as (
    select distinct  -- 実績データにレコード単位の重複があるため排除してから結合
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
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_actuals
)
select
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
    coalesce(s_f_n_m.mapped_name, f_a_d.facility_name) as facility_name
from facility_actuals_distinct as f_a_d
left join USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_name_mappings as s_f_n_m
    on f_a_d.facility_name = s_f_n_m.original_name
  );

