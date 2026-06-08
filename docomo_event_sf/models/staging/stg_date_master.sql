{#-
  日付マスタ staging。BQ: SELECT * FROM raw_date_master のミラー。
  源泉切替: BQ raw_date_master → SF source('raw','RAW_DATE_MASTER')。
  latest_updated_at（アップローダ付与・BQ raw に無い列）は除外して BQ stg とスキーマを揃える。
-#}
select * exclude ("latest_updated_at")
from {{ source('raw', 'RAW_DATE_MASTER') }}
