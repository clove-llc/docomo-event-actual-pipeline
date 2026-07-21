
  create or replace   view USERDB_B_P01_LAK.USER_SMCB_01.int_facility_event_decile_mapping
  
  
  
  
  as (
    with unpivoted as (
    select
        facility_code,
        facility_name,
        'GW' as date_flag,
        gw_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        'お盆' as date_flag,
        obon_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        '三連休' as date_flag,
        three_day_holiday_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        '正月' as date_flag,
        new_year_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        '通常土日' as date_flag,
        regular_weekend_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        '年末' as date_flag,
        year_end_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        '飛び石祝日' as date_flag,
        bridge_holiday_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        '平日' as date_flag,
        weekday_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    union all
    select
        facility_code,
        facility_name,
        'ブラックフライデー' as date_flag,
        black_friday_decile_rank as decile_rank
    from USERDB_B_P01_LAK.USER_SMCB_01.stg_facility_foot_traffic_avg_and_decile_by_flag
    
    
)
select
    facility_code,
    facility_name,
    date_flag,
    decile_rank
from unpivoted
where decile_rank is not null
  );

