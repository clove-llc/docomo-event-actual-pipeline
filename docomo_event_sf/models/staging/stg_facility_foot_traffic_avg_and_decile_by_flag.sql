{#-
  人流平均・デシル staging。BQ: SELECT * FROM raw_facility_foot_traffic_avg_and_decile_by_flag のミラー。
  源泉切替: BQ raw_facility_foot_traffic_avg_and_decile_by_flag（計算済みソース）
           → SF ref('raw_facility_foot_traffic_avg_and_decile_by_flag')（源泉作成層で再現）。
-#}
select
  *
from {{ ref('raw_facility_foot_traffic_avg_and_decile_by_flag') }}
