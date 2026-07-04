
  create or replace   view HARATO.INT.int_facility_event_planning_snapshot
  
  
  
  
  as (
    with date_flags as (
    select s_d_m.date_flag
    from HARATO.STG.stg_date_master as s_d_m
    group by s_d_m.date_flag
),

all_pattern as (
    select
        i_b_p.benchmark_period_key,
        i_b_p.benchmark_period_name,
        i_b_p.period_start_date,
        i_b_p.period_end_date,
        s_f_m.facility_code,
        s_f_m.facility_name,
        s_f_m.po_level,
        s_f_m.regional_office,
        s_f_m.branch_office,
        d_f.date_flag,
        i_f_e_d_m.decile_rank
    from HARATO.STG.stg_facility_master as s_f_m
    cross join HARATO.INT.int_benchmark_periods as i_b_p
    cross join date_flags as d_f
    left join HARATO.INT.int_facility_event_decile_mapping as i_f_e_d_m
        on s_f_m.facility_code = i_f_e_d_m.facility_code
       and d_f.date_flag = i_f_e_d_m.date_flag
),

base as (
    select
        all_pattern.benchmark_period_key,
        all_pattern.benchmark_period_name,
        all_pattern.period_start_date,
        all_pattern.period_end_date,
        all_pattern.facility_code,
        all_pattern.facility_name,
        all_pattern.po_level,
        all_pattern.regional_office,
        all_pattern.branch_office,
        all_pattern.date_flag,
        all_pattern.decile_rank,
        i_f_e_d_a_a.avg_actual,
        i_e_d_b.p10,
        i_e_d_b.p20,
        i_e_d_b.p25,
        i_e_d_b.p30,
        i_e_d_b.p40,
        i_e_d_b.p50,
        i_e_d_b.p60,
        i_e_d_b.p70,
        i_e_d_b.p75,
        i_e_d_b.p90,
        i_e_d_b.max_performance,
        greatest(
            case
                when i_f_e_d_a_a.avg_actual is null or i_f_e_d_a_a.avg_actual < i_e_d_b.p50 then i_e_d_b.p50
                when i_f_e_d_a_a.avg_actual < i_e_d_b.p60 then i_e_d_b.p60
                when i_f_e_d_a_a.avg_actual < i_e_d_b.p70 then i_e_d_b.p70
                when i_f_e_d_a_a.avg_actual < i_e_d_b.p75 then i_e_d_b.p75
                when i_f_e_d_a_a.avg_actual < i_e_d_b.p90 then i_e_d_b.p90
                else i_e_d_b.max_performance
            end,
            1  -- 0の場合は1にする（下限値を1に設定）
        ) as standard_target
    from all_pattern
    left join HARATO.INT.int_event_decile_benchmark as i_e_d_b
        on all_pattern.benchmark_period_key = i_e_d_b.benchmark_period_key
       and all_pattern.date_flag = i_e_d_b.date_flag
       and all_pattern.decile_rank = i_e_d_b.decile_rank
    left join HARATO.INT.int_facility_event_decile_avg_actual as i_f_e_d_a_a
        on all_pattern.benchmark_period_key = i_f_e_d_a_a.benchmark_period_key
       and all_pattern.facility_code = i_f_e_d_a_a.facility_code
       and all_pattern.date_flag = i_f_e_d_a_a.date_flag
       and all_pattern.decile_rank = i_f_e_d_a_a.decile_rank
)

select
    base.*,
    case
        when base.standard_target < base.p60 then base.p60
        when base.standard_target < base.p70 then base.p70
        when base.standard_target < base.p75 then base.p75
        when base.standard_target < base.p90 then base.p90
        else base.max_performance
    end as challenge_target
from base
  );

