select
    facility_code,
    trim(facility_name) as facility_name,
    monthly_event_limit,
    operating_days
from {{ source('raw', 'RAW_FACILITY_SCHEDULE_CONSTRAINTS_MASTER') }}
