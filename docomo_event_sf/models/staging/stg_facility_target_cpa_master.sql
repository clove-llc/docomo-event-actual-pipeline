select
    replace(trim("facility_name"), '・', '･') as "FACILITY_NAME",
    "cpa" as "CPA"
from {{ source('docomo_event_raw', 'RAW_FACILITY_TARGET_CPA_MASTER') }}
