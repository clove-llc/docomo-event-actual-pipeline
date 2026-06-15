select
    trim("facility_name") as "FACILITY_NAME"
from {{ source('raw', 'RAW_EXCLUDED_FACILITY_MASTER') }}
