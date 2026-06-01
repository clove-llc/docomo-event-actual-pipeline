SELECT *
FROM {{ source('docomo_event_raw', 'raw_facility_name_mappings') }}
