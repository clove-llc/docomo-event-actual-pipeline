select
    regional_office_name,
    daily_event_limit,
    operating_days
from {{ source('raw', 'RAW_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER') }}
