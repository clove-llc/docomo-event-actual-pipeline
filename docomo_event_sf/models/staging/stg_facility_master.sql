{#-
  施設マスタ staging。BQ: SELECT * EXCEPT(facility_name), TRIM(facility_name) のミラー。
  源泉切替: BQ raw_facility_master → SF source('raw','RAW_FACILITY_MASTER')。
  - facility_name を TRIM（表記ゆれの前後空白除去）。
  - SF RAW のカラムは小文字クォート識別子のため "facility_name" と明示。
  - latest_updated_at（アップローダ付与・BQ raw に無い列）は除外。
-#}
select
    * exclude ("facility_name", "latest_updated_at"),
    trim("facility_name") as facility_name
from {{ source('raw', 'RAW_FACILITY_MASTER') }}
