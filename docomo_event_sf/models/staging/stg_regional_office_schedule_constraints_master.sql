select *
from {{ source('raw', 'RAW_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER') }}
