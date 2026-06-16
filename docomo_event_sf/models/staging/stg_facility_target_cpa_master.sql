select
    replace(trim(facility_name), '・', '･') as facility_name,
    cpa
from {{ source('raw', 'RAW_FACILITY_TARGET_CPA_MASTER') }}
