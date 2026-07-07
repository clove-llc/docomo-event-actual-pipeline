{#-
  人流平均・デシル staging。BQ: SELECT * FROM raw_facility_foot_traffic_avg_and_decile_by_flag のミラー。
  源泉切替: BQ raw_facility_foot_traffic_avg_and_decile_by_flag（計算済みソース）
           → SF ref('raw_facility_foot_traffic_avg_and_decile_by_flag')（源泉作成層で再現）。
-#}
select
  * replace (
        gw_foot_traffic_avg::number(38,10) as gw_foot_traffic_avg,
        obon_foot_traffic_avg::number(38,10) as obon_foot_traffic_avg,
        three_day_holiday_foot_traffic_avg::number(38,10) as three_day_holiday_foot_traffic_avg,
        new_year_foot_traffic_avg::number(38,10) as new_year_foot_traffic_avg,
        regular_weekend_foot_traffic_avg::number(38,10) as regular_weekend_foot_traffic_avg,
        year_end_foot_traffic_avg::number(38,10) as year_end_foot_traffic_avg,
        bridge_holiday_foot_traffic_avg::number(38,10) as bridge_holiday_foot_traffic_avg,
        weekday_foot_traffic_avg::number(38,10) as weekday_foot_traffic_avg,
        black_friday_foot_traffic_avg::number(38,10) as black_friday_foot_traffic_avg
    )
from {{ ref('raw_facility_foot_traffic_avg_and_decile_by_flag') }}
