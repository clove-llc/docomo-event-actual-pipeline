{#-
  施設名マッピング staging。BQ: SELECT * FROM raw_facility_name_mappings のミラー。
  源泉切替: SF source('raw','RAW_FACILITY_NAME_MAPPINGS')。latest_updated_at は除外。カラム名は大文字へ正規化。
-#}
select
    "original_name" as "ORIGINAL_NAME",
    "mapped_name" as "MAPPED_NAME"
from {{ source('raw', 'RAW_FACILITY_NAME_MAPPINGS') }}
