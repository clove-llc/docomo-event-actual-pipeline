select
    trim(facility_name) as facility_name
from {{ source('raw', 'RAW_EXCLUDED_FACILITY_MASTER') }}
