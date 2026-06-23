select
    * exclude (facility_name),
    trim(facility_name) as facility_name
from {{ source('raw', 'RAW_FACILITY_SCHEDULE_CONSTRAINTS_MASTER') }}
