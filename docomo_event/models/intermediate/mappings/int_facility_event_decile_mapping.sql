WITH unpivoted AS (
  SELECT
    facility_code,
    facility_name,
    date_flag,
    decile_rank
  FROM {{ ref("stg_facility_foot_traffic_avg_and_decile_by_flag") }}
  UNPIVOT (
    decile_rank FOR date_flag IN (
      gw_decile_rank AS 'GW',
      obon_decile_rank AS 'お盆',
      three_day_holiday_decile_rank AS '三連休',
      new_year_decile_rank AS '正月',
      regular_weekend_decile_rank AS '通常土日',
      year_end_decile_rank AS '年末',
      bridge_holiday_decile_rank AS '飛び石祝日',
      weekday_decile_rank AS '平日',
      black_friday_decile_rank AS 'ブラックフライデー'
    )
  )
)

SELECT
  facility_code,
  facility_name,
  date_flag,
  decile_rank
FROM unpivoted
WHERE decile_rank IS NOT NULL
