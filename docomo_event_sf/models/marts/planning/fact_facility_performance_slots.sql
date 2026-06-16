{#-
  BQ fact_facility_performance_slots のミラー。
  施設×日付×ベンチマーク期間 の粒度で、標準/チャレンジ目標値と季節指数掛け版を格納するファクト。
  GW/お盆 は全期間(2025_04_2026_03)のスナップショットを使う。
  季節指数掛け列の丸めは round_bq（BigQuery 互換の2進値 ties-away 丸め）で揃える。
-#}
with planning_snapshot_all_period as (
    select
        facility_code,
        date_flag,
        standard_target as all_period_standard_target,
        challenge_target as all_period_challenge_target,
        p50 as all_period_p50
    from {{ ref('int_facility_event_planning_snapshot') }}
    where benchmark_period_key = '2025_04_2026_03'
),

base as (
    select
        p.benchmark_period_key,
        p.benchmark_period_name,
        p.period_start_date,
        p.period_end_date,
        s_f_m.facility_code,
        s_f_m.facility_name,
        s_f_m.po_level,
        s_f_m.regional_office,
        s_f_m.branch_office,
        s_d_m.date,
        s_d_m.month,
        s_d_m.week_number_monthly,
        s_d_m.date_flag
    from {{ ref('stg_facility_master') }} as s_f_m
    cross join {{ ref('stg_date_master') }} as s_d_m
    cross join {{ ref('int_benchmark_periods') }} as p
),

calc as (
    select
        b.benchmark_period_key,
        b.benchmark_period_name,
        b.period_start_date,
        b.period_end_date,
        b.facility_code,
        b.facility_name,
        b.po_level,
        b.regional_office,
        b.branch_office,
        b.date,
        b.month,
        b.week_number_monthly,
        b.date_flag,
        i_f_t.cpa,
        i_f_t.cpa is not null as has_target_cpa,
        (s_e_f_m.facility_name is not null or i_f_t.cpa > 100000) as is_excluded,
        case
            when b.date_flag in ('GW', 'お盆') then f_e_p_s_all_period.all_period_standard_target
            else f_e_p_s.standard_target
        end as standard_target,
        case
            when b.date_flag in ('GW', 'お盆') then f_e_p_s_all_period.all_period_challenge_target
            else f_e_p_s.challenge_target
        end as challenge_target,
        case
            when b.date_flag in ('GW', 'お盆') then f_e_p_s_all_period.all_period_p50
            else f_e_p_s.p50
        end as p50,
        coalesce(
            i_f_m_w_d_z.avg_z_score,
            i_f_m_d_z.avg_z_score,
            i_f_m_3h.avg_z_score,
            i_f_m_d_g_z.avg_z_score
        ) as zsc
    from base as b
    left join {{ ref('int_facility_event_planning_snapshot') }} as f_e_p_s
        on b.benchmark_period_key = f_e_p_s.benchmark_period_key
       and b.facility_code = f_e_p_s.facility_code
       and b.date_flag = f_e_p_s.date_flag
    left join planning_snapshot_all_period as f_e_p_s_all_period
        on b.facility_code = f_e_p_s_all_period.facility_code
       and b.date_flag = f_e_p_s_all_period.date_flag
    -- 施設 × 月番号 × 週番号 × 日付フラグ
    left join {{ ref('int_facility_monthly_weekday_dateflag_deviation_zscore') }} as i_f_m_w_d_z
        on b.facility_code = i_f_m_w_d_z.facility_code
       and b.month = i_f_m_w_d_z.month
       and b.week_number_monthly = i_f_m_w_d_z.week_number_monthly
       and b.date_flag = i_f_m_w_d_z.date_flag
    -- 施設 × 月番号 × 日付フラグ
    left join {{ ref('int_facility_monthly_dateflag_deviation_zscore') }} as i_f_m_d_z
        on b.facility_code = i_f_m_d_z.facility_code
       and b.month = i_f_m_d_z.month
       and b.date_flag = i_f_m_d_z.date_flag
    -- 施設 × 月 × 三連休
    left join {{ ref('int_facility_monthly_dateflag_deviation_zscore') }} as i_f_m_3h
        on b.facility_code = i_f_m_3h.facility_code
       and b.month = i_f_m_3h.month
       and i_f_m_3h.date_flag = '三連休'
    -- 施設 × 月 × 通常土日
    left join {{ ref('int_facility_monthly_dateflag_deviation_zscore') }} as i_f_m_d_g_z
        on b.facility_code = i_f_m_d_g_z.facility_code
       and b.month = i_f_m_d_g_z.month
       and i_f_m_d_g_z.date_flag = '通常土日'
    left join {{ ref("int_facility_target_cpa_by_facility") }} AS i_f_t
        on b.facility_name = i_f_t.facility_name
    left join {{ ref("stg_excluded_facility_master") }} AS s_e_f_m
        on b.facility_name = s_e_f_m.facility_name
)

select
    benchmark_period_key,
    benchmark_period_name,
    period_start_date,
    period_end_date,
    facility_code,
    facility_name,
    po_level,
    regional_office,
    branch_office,
    date,
    month,
    week_number_monthly,
    date_flag,
    cpa,
    has_target_cpa,
    is_excluded,
    standard_target,
    challenge_target,
    p50,
    {{ round_bq('standard_target * zsc', 0) }} as standard_target_seasonal,
    {{ round_bq('challenge_target * zsc', 0) }} as challenge_target_seasonal,
    {{ round_bq('p50 * zsc', 0) }} as p50_seasonal
from calc
