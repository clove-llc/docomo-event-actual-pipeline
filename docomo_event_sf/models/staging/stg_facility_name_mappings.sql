{#-
  施設名マッピング staging。BQ: SELECT * FROM raw_facility_name_mappings のミラー。
  源泉切替: BQ raw_facility_name_mappings → SF source('raw','RAW_FACILITY_NAME_MAPPINGS')。
  latest_updated_at（アップローダ付与・BQ raw に無い列）は除外。
-#}
select * exclude ("latest_updated_at")
from {{ source('raw', 'RAW_FACILITY_NAME_MAPPINGS') }}
