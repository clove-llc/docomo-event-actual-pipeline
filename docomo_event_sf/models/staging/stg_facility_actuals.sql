{#-
  実績データ staging。BQ: SELECT * EXCEPT(facility_name), TRIM(facility_name) のミラー。
  源泉切替: BQ raw_facility_actuals（計算済みソース）→ SF ref('raw_facility_actuals')
           （源泉作成層で再現した縦持ちテーブル）。
  raw_facility_actuals は明示カラム（大文字）なので facility_name はクォート不要。
-#}
select
    * exclude (facility_name),
    trim(facility_name) as facility_name
from {{ ref('raw_facility_actuals') }}
