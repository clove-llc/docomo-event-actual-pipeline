{#-
  季節指数（偏差値Zスコア）staging。BQ: SELECT * FROM raw_facility_daily_deviation_zscore のミラー。
  源泉切替: BQ raw_facility_daily_deviation_zscore（計算済みソース）
           → SF ref('raw_facility_daily_deviation_zscore')（源泉作成層で再現）。
-#}
select
  * replace (
    z_score::number(38,10) as z_score
  )
from {{ ref('raw_facility_daily_deviation_zscore') }}
