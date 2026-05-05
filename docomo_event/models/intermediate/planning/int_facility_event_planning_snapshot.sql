WITH date_flags AS (
  SELECT s_d_m.date_flag
  FROM {{ ref("stg_date_master_2025_2026") }} AS s_d_m
  GROUP BY
    s_d_m.date_flag
),

all_pattern AS (
  SELECT
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
  FROM {{ ref("stg_facility_master") }} AS s_f_m
  CROSS JOIN {{ ref("int_benchmark_periods") }} AS i_b_p
  CROSS JOIN date_flags AS d_f
  LEFT JOIN {{ ref("int_facility_event_decile_mapping") }} AS i_f_e_d_m
    ON
      s_f_m.facility_code = i_f_e_d_m.facility_code
      AND d_f.date_flag = i_f_e_d_m.date_flag
),

base AS (
  SELECT
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
    GREATEST(
      CASE
        WHEN i_f_e_d_a_a.avg_actual IS NULL OR i_f_e_d_a_a.avg_actual < i_e_d_b.p50 THEN i_e_d_b.p50
        WHEN i_f_e_d_a_a.avg_actual < i_e_d_b.p60 THEN i_e_d_b.p60
        WHEN i_f_e_d_a_a.avg_actual < i_e_d_b.p70 THEN i_e_d_b.p70
        WHEN i_f_e_d_a_a.avg_actual < i_e_d_b.p75 THEN i_e_d_b.p75
        ELSE i_e_d_b.p90
      END,
      1 -- 0の場合は1にする（下限値を1に設定）
    ) AS standard_target
  FROM all_pattern
  LEFT JOIN {{ ref("int_event_decile_benchmark") }} AS i_e_d_b
    ON
      all_pattern.benchmark_period_key = i_e_d_b.benchmark_period_key
      AND all_pattern.date_flag = i_e_d_b.date_flag
      AND all_pattern.decile_rank = i_e_d_b.decile_rank
  LEFT JOIN {{ ref("int_facility_event_decile_avg_actual") }} AS i_f_e_d_a_a
    ON
      all_pattern.benchmark_period_key = i_f_e_d_a_a.benchmark_period_key
      AND all_pattern.facility_code = i_f_e_d_a_a.facility_code
      AND all_pattern.date_flag = i_f_e_d_a_a.date_flag
      AND all_pattern.decile_rank = i_f_e_d_a_a.decile_rank
)

SELECT
  base.*,
  CASE
    WHEN base.standard_target < base.p60 THEN base.p60
    WHEN base.standard_target < base.p70 THEN base.p70
    WHEN base.standard_target < base.p75 THEN base.p75
    WHEN base.standard_target < base.p90 THEN base.p90
    ELSE base.max_performance
  END AS challenge_target
FROM base
