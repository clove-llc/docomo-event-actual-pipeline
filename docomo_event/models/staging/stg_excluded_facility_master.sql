SELECT TRIM(facility_name) AS facility_name
FROM {{ source('docomo_event_raw', 'raw_excluded_facility_master') }}
